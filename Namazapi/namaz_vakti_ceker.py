import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re

# Renk kodları
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'

# Global il değişkeni
SELECTED_IL = None

def save_url_to_file(url, il_adi):
    # URL'leri kaydedeceğimiz dosya yolu
    url_file = r"C:\Users\Lyrox\Desktop\Namazapi\girilen_urller.txt"
    
    # Klasörün var olduğundan emin ol
    os.makedirs(os.path.dirname(url_file), exist_ok=True)
    
    # Dosya boşsa veya yoksa il adını başlık olarak ekle
    if not os.path.exists(url_file) or os.path.getsize(url_file) == 0:
        with open(url_file, 'w', encoding='utf-8') as f:
            f.write(f"                                       ##{il_adi}\n\n")
    
    # Yeni il için başlık ekle
    with open(url_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if f"##{il_adi}" not in content and f"# {il_adi}" not in content:
            with open(url_file, 'a', encoding='utf-8') as f:
                f.write(f"                                       # {il_adi}\n")
    
    # Dosya varsa son numarayı bul, yoksa 1'den başla
    current_number = 1
    if os.path.exists(url_file):
        with open(url_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                try:
                    # Başlık satırlarını atla
                    data_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
                    if data_lines:
                        last_line = data_lines[-1].strip()
                        if last_line and last_line[0].isdigit():  # Sayı ile başlıyorsa
                            current_number = int(last_line.split('.')[0]) + 1
                except:
                    current_number = len([l for l in lines if l.strip() and not l.strip().startswith('#')]) + 1
    
    # URL'yi dosyaya ekle
    with open(url_file, 'a', encoding='utf-8') as f:
        f.write(f"{current_number}. {url}\n")

def convert_turkish_chars(text):
    # Türkçe karakterleri ASCII karakterlere dönüştür
    tr_chars = {'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
                'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'}
    for tr_char, eng_char in tr_chars.items():
        text = text.replace(tr_char, eng_char)
    return text

def clean_district_name(text):
    # İlçe adından tek harf sonekleri temizle
    alphabet = 'abcçdefgğhıijklmnoöprsştuüvwxyz'
    text = text.lower().strip()
    
    # Her harf için kontrol et
    for letter in alphabet:
        if text.endswith(f" {letter}"):
            text = text[:-2].strip()  # Son harf ve boşluğu kaldır
        if text.endswith(f"-{letter}"):
            text = text[:-2].strip()  # Son harf ve tireyi kaldır
        if text.endswith(f"({letter})"):
            text = text[:-3].strip()  # Son harf ve parantezleri kaldır
            
    return text.strip()

def get_prayer_times(url, retry=True):
    try:
        # URL'den veriyi çek
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP hatalarını kontrol et
        html_content = response.text
        
    except requests.RequestException as e:
        print(f"{Colors.RED}Hata: Veriler çekilemedi: {str(e)}{Colors.RESET}")
        if retry:
            print(f"{Colors.GREEN}Tekrar deneniyor...{Colors.RESET}")
            return get_prayer_times(url, retry=False)  # Bir kez daha dene
        return None
    
    # HTML içeriğini parse et
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # URL'den ilçe adını al
    # Örnek URL: https://namazvakitleri.diyanet.gov.tr/tr-TR/9521/aralik-icin-namaz-vakti
    url_parts = url.split('/')
    if len(url_parts) >= 2:
        location_part = url_parts[-1]  # "aralik-icin-namaz-vakti"
        ilce = location_part.split('-icin-namaz-vakti')[0]  # "aralik"
        ilce = ilce.replace('-', ' ')  # Tire işaretlerini boşluğa çevir
        ilce = clean_district_name(ilce)  # (v) ve v eklerini temizle
        
        # Global il değişkenini kullan
        global SELECTED_IL
        il = SELECTED_IL
        
        # Eğer ilçe adı il adıyla aynıysa merkez olarak değiştir
        if ilce.lower() == il.lower():
            ilce = "merkez"
    else:
        print(f"{Colors.RED}Hata: URL'den ilçe adı alınamadı.{Colors.RESET}")
        return None
    
    # İl ve ilçe adını düzgün formatlayalım
    il = convert_turkish_chars(il).title()  # İl adını düzgün formatlayalım
    ilce = convert_turkish_chars(ilce).lower()  # İlçe adını küçük harfe çevirelim
    
    # Yıllık namaz vakitlerini içeren tabloyu bul
    tables = soup.find_all('table')
    prayer_table = None
    max_rows = 0
    
    for table in tables:
        rows = table.find_all('tr')
        if len(rows) > max_rows:  # En çok satırı olan tabloyu seç (yıllık tablo)
            header_cells = rows[0].find_all(['th', 'td']) if rows else []
            if len(header_cells) >= 8:  # En az 8 sütun olmalı
                header_texts = [cell.get_text(strip=True) for cell in header_cells]
                if 'İmsak' in header_texts and 'Güneş' in header_texts:  # Namaz vakti tablosu olduğundan emin ol
                    max_rows = len(rows)
                    prayer_table = table
    
    if not prayer_table:
        print(f"{Colors.RED}Hata: Yıllık namaz vakitleri tablosu bulunamadı.")
        print("Bulunan tablolar ve satır sayıları:")
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            print(f"Tablo {i+1}: {len(rows)} satır{Colors.RESET}")
        return None
    
    # Klasör yolunu ayarla
    folder_name = r"C:\Users\Lyrox\Documents\GitHub\vakitler\vakitler"
    
    # Klasörü oluştur (eğer yoksa)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Dosya adını oluştur
    file_name = os.path.join(folder_name, f"{il}_{ilce}.txt")
    print(f"Oluşturulan dosya adı: {file_name}")  # Debug için dosya adını yazdır
    
    # Verileri dosyaya kaydet
    with open(file_name, 'w', encoding='utf-8') as f:
        # Tüm satırları işle
        rows = prayer_table.find_all('tr')
        for row in rows:
            cols = row.find_all(['th', 'td'])
            if len(cols) >= 8:  # Tüm sütunların var olduğundan emin ol
                # Her sütundaki metni al ve temizle
                values = [col.get_text(strip=True) for col in cols[:8]]
                
                # Boş değer kontrolü
                if any(values):  # Eğer en az bir değer doluysa
                    # HTML formatında yaz
                    f.write("                                            <tr>\n")
                    f.write(f"                                                <td>{values[0]}</td>\n")
                    f.write(f"                                                <td>{values[1]}</td>\n")
                    f.write(f"                                                <td>{values[2]}</td>\n")
                    f.write(f"                                                <td>{values[3]}</td>\n")
                    f.write(f"                                                <td>{values[4]}</td>\n")
                    f.write(f"                                                <td>{values[5]}</td>\n")
                    f.write(f"                                                <td>{values[6]}</td>\n")
                    f.write(f"                                                <td>{values[7]}</td>\n")
                    f.write("                                            </tr>\n")
    
    return file_name

if __name__ == "__main__":
    print("Namaz vakitlerini indirme programı - Çıkmak için 'q' yazın")
    print("-" * 50)
    
    # Klasör yolunu ayarla
    folder_name = r"C:\Users\Lyrox\Documents\GitHub\vakitler\vakitler"
    
    # Klasörü oluştur (eğer yoksa)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Program başlangıcında il adını al
    while True:
        SELECTED_IL = input("\nİl adını girin: ").strip()
        if SELECTED_IL:
            print(f"{Colors.GREEN}İl adı '{SELECTED_IL}' olarak ayarlandı.{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}İl adı boş olamaz!{Colors.RESET}")
    
    while True:
        url = input("\nDiyanet namaz vakitleri URL'sini girin (çıkmak için 'q'): ").strip()
        
        if url.lower() == 'q':
            print("\nProgram sonlandırılıyor...")
            break
            
        if not url:  # Boş girdi kontrolü
            print(f"{Colors.RED}URL boş olamaz!{Colors.RESET}")
            continue
            
        # URL'yi dosyaya kaydet
        save_url_to_file(url, SELECTED_IL)
            
        file_path = get_prayer_times(url, retry=True)
        if file_path:
            print(f"\n{Colors.GREEN}Namaz vakitleri başarıyla kaydedildi: {file_path}{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}Namaz vakitleri alınırken bir hata oluştu.{Colors.RESET}")
            
    print("\nProgram sonlandırıldı.") 