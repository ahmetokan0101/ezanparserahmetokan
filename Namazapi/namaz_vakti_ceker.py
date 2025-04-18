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
    try:
        # URL'leri kaydedeceğimiz dosya yolu
        url_file = os.path.join(os.getcwd(), "girilen_urller.txt")
        print(f"\nURL dosya yolu: {url_file}")
        
        # Dosya boşsa veya yoksa il adını başlık olarak ekle
        if not os.path.exists(url_file) or os.path.getsize(url_file) == 0:
            print("Yeni dosya oluşturuluyor...")
            with open(url_file, 'w', encoding='utf-8') as f:
                f.write(f"                                       ##{il_adi}\n\n")
                print(f"İl başlığı eklendi: {il_adi}")
        
        # Yeni il için başlık ekle
        with open(url_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if f"##{il_adi}" not in content and f"# {il_adi}" not in content:
                print(f"Yeni il başlığı ekleniyor: {il_adi}")
                with open(url_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n                                       # {il_adi}\n")
        
        # Dosya varsa son numarayı bul, yoksa 1'den başla
        current_number = 1
        if os.path.exists(url_file):
            with open(url_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    try:
                        data_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
                        if data_lines:
                            last_line = data_lines[-1].strip()
                            if last_line and last_line[0].isdigit():
                                current_number = int(last_line.split('.')[0]) + 1
                                print(f"Son URL numarası: {current_number-1}")
                    except Exception as e:
                        print(f"Numara bulma hatası: {e}")
                        current_number = len([l for l in lines if l.strip() and not l.strip().startswith('#')]) + 1
        
        # URL'yi dosyaya ekle
        print(f"URL ekleniyor: {current_number}. {url}")
        with open(url_file, 'a', encoding='utf-8') as f:
            f.write(f"{current_number}. {url}\n")
        print("URL başarıyla eklendi!")
        
    except Exception as e:
        print(f"{Colors.RED}URL kaydetme hatası: {str(e)}{Colors.RESET}")

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html_content = response.text
        
    except requests.RequestException as e:
        print(f"{Colors.RED}Hata: Veriler çekilemedi: {str(e)}{Colors.RESET}")
        if retry:
            print(f"{Colors.GREEN}Tekrar deneniyor...{Colors.RESET}")
            return get_prayer_times(url, retry=False)
        return None
    
    # HTML içeriğini parse et
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # URL'den ilçe adını al
    url_parts = url.split('/')
    if len(url_parts) >= 2:
        location_part = url_parts[-1]
        ilce = location_part.split('-icin-namaz-vakti')[0]
        ilce = ilce.replace('-', ' ')
        ilce = clean_district_name(ilce)
        
        global SELECTED_IL
        il = SELECTED_IL
        
        if ilce.lower() == il.lower():
            ilce = "merkez"
    else:
        print(f"{Colors.RED}Hata: URL'den ilçe adı alınamadı.{Colors.RESET}")
        return None
    
    # İl ve ilçe adını düzgün formatlayalım
    il = convert_turkish_chars(il).title()
    ilce = convert_turkish_chars(ilce).lower()
    
    # Namaz vakitlerini içeren div'i bul
    prayer_divs = soup.find_all('div', {'class': 'table-responsive'})
    prayer_table = None
    max_rows = 0

    # En uzun tabloyu bul (yıllık tablo)
    for div in prayer_divs:
        table = div.find('table')
        if table:
            rows = table.find_all('tr')
            if len(rows) > max_rows:
                max_rows = len(rows)
                prayer_table = table
    
    if not prayer_table:
        print(f"{Colors.RED}Hata: Yıllık namaz vakitleri tablosu bulunamadı.{Colors.RESET}")
        print("Bulunan tablo sayısı:", len(prayer_divs))
        return None

    print(f"{Colors.GREEN}Bulunan tablo satır sayısı: {max_rows}{Colors.RESET}")
    
    # Klasör yolunu ayarla
    folder_name = os.path.join(os.getcwd(), "vakitler")
    
    # Klasörü oluştur (eğer yoksa)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Dosya adını oluştur
    file_name = os.path.join(folder_name, f"{il}_{ilce}.txt")
    print(f"Oluşturulan dosya adı: {file_name}")
    
    # Verileri dosyaya kaydet
    with open(file_name, 'w', encoding='utf-8') as f:
        # Tüm satırları işle
        rows = prayer_table.find_all('tr')
        for row in rows:
            cols = row.find_all(['th', 'td'])
            if len(cols) >= 8:
                values = [col.get_text(strip=True) for col in cols[:8]]
                if any(values):
                    f.write("                                            <tr>\n")
                    for value in values:
                        f.write(f"                                                <td>{value}</td>\n")
                    f.write("                                            </tr>\n")
    
    return file_name

if __name__ == "__main__":
    print("Namaz vakitlerini indirme programı - Çıkmak için 'q' yazın")
    print("-" * 50)
    
    # Klasör yolunu ayarla
    folder_name = os.path.join(os.getcwd(), "vakitler")
    
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