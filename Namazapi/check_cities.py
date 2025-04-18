import requests
import json
from typing import List, Dict, Tuple
import re
import time
import os
from urllib.parse import quote
from datetime import datetime

# GitHub'daki verilerin URL'si
GITHUB_BASE_URL = "https://github.com/ahmetokan0101/VakitlerEzanvaktim/raw/main/Ezanvaktimvakitler"

def normalize_string(text: str, is_city: bool = False) -> str:
    """Türkçe karakterleri normalize eder ve harf büyüklüğünü ayarlar"""
    tr_chars = {
        'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
        'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C'
    }
    for tr_char, eng_char in tr_chars.items():
        text = text.replace(tr_char, eng_char)
    
    # İl adı için ilk harfi büyük, ilçe adı için küçük yap
    if text:
        if is_city:
            text = text[0].upper() + text[1:].lower()
        else:
            text = text[0].lower() + text[1:]
    return text

def test_url(city: str, district: str) -> Tuple[bool, str, str]:
    """Belirli bir il ve ilçe için URL'yi test eder"""
    city_normalized = normalize_string(city, is_city=True)
    district_normalized = normalize_string(district)
    
    # URL'yi oluştur
    url = f"{GITHUB_BASE_URL}/{city_normalized}_{district_normalized}.txt"
    merkez_url = f"{GITHUB_BASE_URL}/{city_normalized}_merkez.txt"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True, url, "İlçe URL'si"
        else:
            # Merkez ilçeyi dene
            merkez_response = requests.get(merkez_url)
            if merkez_response.status_code == 200:
                return True, merkez_url, "Merkez URL'si"
            return False, url, "İlçe URL'si (Başarısız)"
    except Exception as e:
        return False, f"{url} (Hata: {str(e)})", "Hata"

def save_missing_to_file(missing: List[Tuple[str, List[Tuple[str, str, str]]]]) -> None:
    """Eksik il ve ilçeleri proje dizinine kaydeder"""
    try:
        # Dosya adını oluştur
        filename = "eksik_il_ilceler.txt"
        print(f"\nDosya oluşturuluyor: {filename}")
        
        # Dosyayı oluştur ve yaz
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== EKSİK İL VE İLÇELER ===\n\n")
            f.write(f"Kontrol Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
            
            for city, districts in missing:
                f.write(f"\n{city}:\n")
                for district, url, url_type in districts:
                    f.write(f"  - {district}\n")
                    f.write(f"    URL: {url}\n")
                    f.write(f"    Tip: {url_type}\n")
        
        print(f"Dosya başarıyla kaydedildi: {filename}")
        
    except Exception as e:
        print(f"Hata: {e}")

def save_available_to_file(available: List[Tuple[str, List[Tuple[str, str, str]]]]) -> None:
    """Mevcut il ve ilçeleri proje dizinine kaydeder"""
    try:
        # Dosya adını oluştur
        filename = "mevcut_il_ilceler.txt"
        print(f"\nDosya oluşturuluyor: {filename}")
        
        # Dosyayı oluştur ve yaz
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== MEVCUT İL VE İLÇELER ===\n\n")
            f.write(f"Kontrol Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
            
            for city, districts in available:
                f.write(f"\n{city}:\n")
                for district, url, url_type in districts:
                    f.write(f"  - {district}\n")
                    f.write(f"    URL: {url}\n")
                    f.write(f"    Tip: {url_type}\n")
        
        print(f"Dosya başarıyla kaydedildi: {filename}")
        
    except Exception as e:
        print(f"Hata: {e}")

def check_cities(cities_data: Dict[str, List[str]]) -> None:
    """Tüm il ve ilçeleri sırayla test eder"""
    try:
        total_cities = len(cities_data)
        total_districts = sum(len(districts) for districts in cities_data.values())
        tested = 0
        
        # Dosyayı oluştur
        error_file = "calismayan_ilceler.txt"
        
        # Dosya başlığını yaz
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write("=== ÇALIŞMAYAN İLÇELER ===\n\n")
            f.write(f"Kontrol Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
        
        print(f"\nToplam {total_cities} il ve {total_districts} ilçe kontrol edilecek...\n")
        print(f"Çalışmayan ilçeler dosyası: {error_file}\n")
        
        for city, districts in cities_data.items():
            print(f"\n=== {city} İli Kontrol Ediliyor ===")
            
            for district in districts:
                tested += 1
                print(f"\nİlerleme: {tested}/{total_districts} ({tested/total_districts*100:.1f}%)")
                print(f"Kontrol Edilen: {city} - {district}")
                
                success, url, url_type = test_url(city, district)
                print(f"Oluşturulan URL: {url}")
                print(f"URL Tipi: {url_type}")
                print(f"Durum: {'✅ ÇALIŞIYOR' if success else '❌ ÇALIŞMIYOR'}")
                
                # Sadece çalışmayan ilçeleri dosyaya yaz
                if not success:
                    with open(error_file, 'a', encoding='utf-8') as f:
                        f.write(f"\n{city} - {district}:\n")
                        f.write(f"  URL: {url}\n")
                        f.write(f"  Tip: {url_type}\n")
                    print(f"-> Çalışmayan ilçeler dosyasına eklendi: {error_file}")
                
                print("-" * 80)
                
                # GitHub API limitini aşmamak için kısa bir bekleme
                time.sleep(0.1)
        
        # Sonuçları yazdır
        print("\n\n=== KONTROL SONUÇLARI ===")
        print(f"\nToplam Test Edilen: {tested}")
        print(f"Çalışmayan ilçeler şu dosyaya kaydedildi: {error_file}")
        
    except Exception as e:
        print(f"Hata: {e}")

def main():
    # Projedeki il ve ilçe verilerini oku
    try:
        with open('lib/data/cities.dart', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Dart dosyasından verileri çıkar
        pattern = r'City\(name: \'([^\']+)\', districts: \[([^\]]+)\]\)'
        matches = re.findall(pattern, content)
        
        cities_data = {}
        for city, districts_str in matches:
            districts = [d.strip().strip("'") for d in districts_str.split(',')]
            cities_data[city] = districts
            
        # Tüm il ve ilçeleri kontrol et
        check_cities(cities_data)
        
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main() 