import colorama
from colorama import Fore, Style
import pyfiglet
import json
import asyncio
import sys

from kontenjan import Kontenjan
from basvuru import Basvuru

json_dosyasi = "config.json"

class Main():
    def __init__(self, bilgiler):
        # Otomatik renk resetleme işlemi
        colorama.init(autoreset=True)  
        
        self.kontenjan = Kontenjan(bilgiler)
        self.basvuru = Basvuru(bilgiler)
        
        self.saniye = int(bilgiler["saniye"])
        self.bilgiler = bilgiler
        
    async def basla(self):
        ascii_text = pyfiglet.figlet_format("Zeysnepk") 
        print(Fore.MAGENTA + Style.BRIGHT + ascii_text)
        await asyncio.sleep(0.2)
        print(Fore.YELLOW + "[👻] Merhaba...")
        await asyncio.sleep(0.2)
        print(Fore.LIGHTWHITE_EX + "[👾] Başlamadan önceee...")
        await asyncio.sleep(0.2)
        print(Fore.CYAN + "[🫷] Lütfen sayfaların açılmasını bekleyiniz!!!")
        #await asyncio.sleep(0.2)
        try:
            # kontenjan.basla() ve basvuru.basla() fonksiyonlarını eş zamanlı çalıştır
            await asyncio.gather(
            # headless=True ile arka planda çalıştırır
            self.kontenjan.basla(headless=True), 
            self.basvuru.basla(headless=True)
            )  
            # Arka planda E-Devlet girişi yap
            # Captcha varsa çözülene kadar bekler
            await self.basvuru.e_devlet_giris()
            print(Fore.GREEN + f"[🥳] Captcha çözüldü devam edebilirizzz")
        except Exception as e:
            print(Fore.RED + f"[❌] Hata, sayfalara erişilemedi, bilgilerinizi kontrol ediniz: {str(e)}")
            
            # Eğer `self.basvuru` başlatılmışsa bitir
            if hasattr(self, "browser") and self.basvuru:
                await self.basvuru.bitir()

            # Eğer `self.kontenjan` başlatılmışsa bitir
            if hasattr(self, "browser") and self.kontenjan:
                await self.kontenjan.bitir()
            # Başarısız çıkış -> 1
            sys.exit(1)
            
        while True: 
            yanit = input(Fore.BLUE + "[👀] Bilgileri değiştirmek ister misin???(Y/n) : ")
            if yanit.lower() == 'y':
                print("Tamam Değiştirelim O Zamannn")
                
                while True:
                    secim = await self.bilgi_degistir()
                    ret = await self.secim_yap(secim)
                    
                    if ret.lower() == 't':
                        print(Fore.GREEN + "[🤩] Başarılı Bir Şekilde Güncelleme Yapıldı!")
                        await asyncio.sleep(0.2)
                        print(Fore.LIGHTCYAN_EX + "[🙀] Kontenjan Kontrolüne Başlıyoruuuz...!")
                        await self.kontrol_et()
                        break
                    elif ret.lower() == 'd':
                        await asyncio.sleep(0.2)
                    else:
                        print(Fore.RED + "[❌] Geçersiz giriş. Lütfen tekrar deneyin.")
                        await asyncio.sleep(0.2)
                        continue
                break
                
            elif yanit.lower() == 'n':
                print(Fore.LIGHTMAGENTA_EX + "[🎉] O zaman başlıyoruuz!!!")
                await asyncio.sleep(0.2)
                await self.kontrol_et()
                break
            
            else:
                print(Fore.RED + "[👿] Geçersiz giriş. Lütfen tekrar deneyin.")
                await asyncio.sleep(0.2)
                
    async def kontrol_et(self):
        while True:
            print(Fore.YELLOW + "[👀] Kontenjan Kontrolü...")
            await asyncio.sleep(0.2)
            try:
                kontenjan_sayisi = await self.kontenjan.kontenjan_kontrol()
            except Exception as e:
                # Sayfa, onay gününde girişlere kapalı olur
                print(Fore.RED + f"[❌] Hata, sayfa kapalı olabilir: {str(e)}")
                await self.kontenjan.bitir()
                break
            await self.kontenjan.bitir()
            print(Fore.GREEN + f"[🔢] Kontenjan sayısı: {kontenjan_sayisi}")
            await asyncio.sleep(0.2)
            
            # Eğer kontenjan varsa basvuru yap
            if int(kontenjan_sayisi) > 0:
                print(Fore.CYAN + f"[⭐️] Kontenjan Bulundu Başvuruya Başlanıyor...")
                mesaj = await self.basvuru.basvur()
                print(Fore.RED + f"[❓] Başvuru Sonucu: {mesaj}")
            else:
                print(Fore.YELLOW + f"[⏰] {self.saniye} saniye sonra tekrar kontrol edilecek!")
            await asyncio.sleep(self.saniye)
            
    async def bilgi_degistir(self):
        print(Fore.LIGHTYELLOW_EX + "[🚀] Değiştirebileceğin Alanlar")
        await asyncio.sleep(0.2)
        print(Fore.YELLOW + "------------------------------------------------")
        await asyncio.sleep(0.2)
        
        print(Fore.MAGENTA + """ 
[1]  TC KİMLİK NUMARASI
[2]  OKUL NUMARASI
[3]  İL
[4]  İLÇE
[5]  KURUM TÜRÜ
[6]  KAYIT ALANI
[7]  OKUL
[8]  SINIF
[9]  E-DEVLET KİMLİK NO
[10] E-DEVLET ŞİFRE
[11] NAKİL NEDENİ
[12] GİDİLECEK OKUL TÜRÜ
[13] GİDİLECEK OKUL ALANI
[14] GİDİLECEK OKUL DALI
[15] GİDİLECEK OKUL
[16] YABANCI DİL
[17] KONTROL ARALIK SIKLIĞI
        """)
        await asyncio.sleep(0.2)
        print(Fore.RED + "[🤓] NOT: Her şeyi doldurmak zorunda değilsiniz boş kalabilir!!!")
        await asyncio.sleep(0.2)
        print(Fore.LIGHTYELLOW_EX + "[❎] Çıkış yapmak için 'x' e basınız!")
        return input("\n" + Fore.GREEN + "Lütfen seçimini giriniz(!sayı!) : ")
    
    async def secenek_gir(self, degisken, ad, json_ad):
        # Giriş verilerinde uyuşmazlık varsa hata döndür
        if degisken == []:
            print(Fore.RED + f"[🔺] Hata, {ad} alınamadı!!")
            await self.kontenjan.bitir()
            await self.basvuru.bitir()
            sys.exit(1)
        # Seçeneklerin listelenip indexlerine göre kullanıcıya sunulur
        for idx, secenek in enumerate(degisken, start=1):
            print(f"[{idx}] {secenek}")
        secenek = int(input("\n" + Fore.LIGHTRED_EX + f"{ad} Seçiniz: "))
        self.bilgiler[f"{json_ad}"] = degisken[secenek - 1]
    
    async def secim_yap(self, secim):
        print()
        try:
            match secim:
                case '1':
                    self.bilgiler["kimlik_no"] = input("TC Kimlik No Girin: ")
                case '2':
                    self.bilgiler["okul_no"] = input("Okul No Girin: ")
                case '3':
                    iller = await self.kontenjan.illeri_listele()
                    await self.secenek_gir(iller, "İl", "il")
                case '4':
                    ilceler = await self.kontenjan.ilceleri_listele()
                    await self.secenek_gir(ilceler, "İlce", "ilce")
                case '5':
                    kurum_turu = await self.kontenjan.kurum_turleri_listele()
                    await self.secenek_gir(kurum_turu, "Kurum Türü", "kurum_turu")
                case '6':
                    alanlar = await self.kontenjan.kayit_alanlari_listele()
                    await self.secenek_gir(alanlar, "Kayıt Alanı", "kayit_alani")
                case '7':
                    okullar = await self.kontenjan.okullari_listele()
                    await self.secenek_gir(okullar, "Okul", "okul")
                case '8':
                    self.bilgiler["sinif"] = input("Sınıf Girin: ")
                case '9':
                    self.bilgiler["edevlet_no"] = input("E-Devlet Kimlik No Girin: ")
                case '10':
                    self.bilgiler["edevlet_sifre"] = input("E-Devlet Şifre Girin: ")
                case '11':
                    nedenler = await self.basvuru.nedenleri_listele()
                    await self.secenek_gir(nedenler, "Neden", "nakil_nedeni")
                case '12':
                    turler = await self.basvuru.turleri_listele()
                    await self.secenek_gir(turler, "Tür", "gidilecek_tur")
                case '13':
                    alanlar = await self.basvuru.alanlari_listele()
                    await self.secenek_gir(alanlar, "Okul Alanı", "gidilecek_alan")
                case '14':
                    dallar = await self.basvuru.dallari_listele()
                    await self.secenek_gir(dallar, "Okul Dalı", "gidilecek_dal")
                case '15':
                    okullar = await self.basvuru.okullari_listele()
                    await self.secenek_gir(okullar, "Okul", "gidilecek_okul")
                case '16':
                    diller = await self.basvuru.dilleri_listele()
                    await self.secenek_gir(diller, "Dil", "yabanci_dil")
                case '17':
                    self.saniye = int(input("Kontrol Aralık Sıklığı (saniye): "))
                    self.bilgiler["saniye"] = self.saniye
                case 'x' | 'X':
                    await self.kontenjan.bitir()
                    await self.basvuru.bitir()
                    # Başarılı çıkış -> 0
                    sys.exit(0)
                case _:
                    print(Fore.LIGHTRED_EX + "Geçersiz Seçim!")
                    await asyncio.sleep(0.5)
                    return await self.secim_yap(secim)
        except Exception as e:
            print(Fore.RED + f"[❌] Hata, sayfada giriş yapılamıyor olabilir: {str(e)}")
            await self.kontenjan.bitir()
            sys.exit(1)
                
        await asyncio.sleep(0.2)
        # Girilen verileri json dosyasına yazdır
        with open(json_dosyasi, "w", encoding="utf-8") as file:
            json.dump(self.bilgiler, file, indent=4, ensure_ascii=False)
        
        return input("\n" + Fore.LIGHTRED_EX + "Tamam mı, Devam mı??(T/D): ")
        
async def main_basla():
    await main.basla()
        
if __name__ == "__main__":
    # Bilgileri json dosyasından oku
    with open(json_dosyasi, 'r', encoding='utf-8') as file:
        json_bilgiler = json.load(file)
        
    main = Main(json_bilgiler)
    asyncio.run(main_basla())