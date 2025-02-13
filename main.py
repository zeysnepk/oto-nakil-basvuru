import colorama
from colorama import Fore, Style
import pyfiglet
import json
import asyncio

from kontenjan import Kontenjan
from basvuru import Basvuru

class Main():
    def __init__(self, bilgiler):
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
        print(Fore.GREEN + "[👾] Başlamadan önceee...")
        #await asyncio.sleep(0.2)
        await asyncio.gather(
        self.kontenjan.basla(headless=True),
        self.basvuru.basla(headless=True)
        )  
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
                        print(Fore.RED + "[��] Geçersiz giriş. Lütfen tekrar deneyin.")
                        await asyncio.sleep(0.2)
                        continue
                break
                
            elif yanit.lower() == 'n':
                print(Fore.LIGHTMAGENTA_EX + "[🎉] O zaman başlıyoruuz!!!")
                await self.kontrol_et()
                break
            
            else:
                print(Fore.RED + "[👿] Geçersiz giriş. Lütfen tekrar deneyin.")
                await asyncio.sleep(0.2)
                
    async def kontrol_et(self):
        while True:
            print(Fore.YELLOW + "[👀] Kontenjan Kontrolü...")
            await asyncio.sleep(0.2)
            kontenjan_sayisi = await self.kontenjan.kontenjan_kontrol()
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
        """)
        await asyncio.sleep(0.2)
        print(Fore.RED + "[🤓] NOT: Her şeyi doldurmak zorunda değilsiniz boş kalabilir!!!")
        await self.basvuru.e_devlet_giris()
        return input("\n" + Fore.GREEN + "Lütfen seçimini giriniz(!sayı!) : ")
    
    async def secim_yap(self, secim):
        match secim:
            case '1':
                self.bilgiler["kimlik_no"] = input("TC Kimlik No Girin: ")
            case '2':
                self.bilgiler["okul_no"] = input("Okul No Girin: ")
            case '3':
                iller = await self.kontenjan.illeri_listele()
                print()
                for idx, secenek in enumerate(iller, start=1):
                    print(f"[{idx}] {secenek}")
                secenek = int(input("\n" + Fore.LIGHTRED_EX + "İl Seçiniz: "))
                self.bilgiler["il"] = iller[secenek - 1]
            case '4':
                ilceler = await self.kontenjan.ilceleri_listele()
                print()
                for idx, secenek in enumerate(ilceler, start=1):
                    print(f"[{idx}] {secenek}")
                secenek = int(input("\n" + Fore.LIGHTRED_EX + "İlçe Seçiniz: "))
                self.bilgiler["ilce"] = ilceler[secenek - 1]
            case '5':
                kurum_turu = await self.kontenjan.kurum_turleri_listele()
                print()
                for idx, secenek in enumerate(kurum_turu, start=1):
                    print(f"[{idx}] {secenek}")
                secenek = int(input("\n" + Fore.LIGHTRED_EX + "Kurum Türü Seçiniz: "))
                self.bilgiler["kurum_turu"] = kurum_turu[secenek - 1]
            case '6':
                alanlar = await self.kontenjan.kayit_alanlari_listele()
                print()
                for idx, secenek in enumerate(alanlar, start=1):
                    print(f"[{idx}] {secenek}")
                secenek = int(input("\n" + Fore.LIGHTRED_EX + "Kayıt Alanı Seçiniz: "))
                self.bilgiler["kayit_alani"] = alanlar[secenek - 1]
            case '7':
                okullar = await self.kontenjan.okullari_listele()
                print()
                for idx, secenek in enumerate(okullar, start=1):
                    print(f"[{idx}] {secenek}")
                secenek = int(input("\n" + Fore.LIGHTRED_EX + "Okul Seçiniz: "))
                self.bilgiler["okul"] = okullar[secenek - 1]
            case '8':
                self.bilgiler["sinif"] = input("Sınıf Girin: ")
            case '9':
                self.bilgiler["edevlet_no"] = input("E-Devlet Kimlik No Girin: ")
            case '10':
                self.bilgiler["edevlet_sifre"] = input("E-Devlet Şifre Girin: ")
            case '11':
                nedenler = await self.basvuru.nedenleri_listele()
                print()
                for idx, secenek in enumerate(nedenler, start=1):
                    print(f"[{idx}] {secenek}")
                secenek = int(input("\n" + Fore.LIGHTRED_EX + "Neden Seçiniz: "))
                self.bilgiler["nakil_nedeni"] = nedenler[secenek - 1]
        await asyncio.sleep(0.2)
        with open("bilgiler.json", "w", encoding="utf-8") as file:
            json.dump(self.bilgiler, file, indent=4, ensure_ascii=False)
        
        return input("\n" + Fore.LIGHTRED_EX + "Tamam mı, Devam mı??(T/D): ")
        
async def main_basla():
    await main.basla()
        
if __name__ == "__main__":
    # Bilgileri json dosyasından oku
    with open("bilgiler.json", 'r', encoding='utf-8') as file:
        json_bilgiler = json.load(file)
        
    main = Main(json_bilgiler)
    asyncio.run(main_basla())