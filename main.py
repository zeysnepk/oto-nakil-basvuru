import colorama
from colorama import Fore, Style
import pyfiglet
import json
import asyncio
import sys
import socket

from kontenjan import Kontenjan
from basvuru import Basvuru

json_dosyasi = "config.json"

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Main():
    def __init__(self, bilgiler):
        # Mail işlemleri için bilgileri çek
        self.mail_gonderen = bilgiler["mail_gonderen"]
        self.sifre = bilgiler["mail_app_sifre"]
        self.mail_alan = bilgiler["mail_alan"]
        # Otomatik renk resetleme işlemi
        colorama.init(autoreset=True)  
        
        self.kontenjan = Kontenjan(bilgiler)
        self.basvuru = Basvuru(bilgiler)
        
        self.saniye = int(bilgiler["saniye"])
        self.bilgiler = bilgiler
        
        self.basvuru_acik = False
    
    async def yanit_bekle(self):
        try:
            yanit = await asyncio.wait_for(
                asyncio.to_thread(input, Fore.BLUE + "[👀] Bilgileri değiştirmek ister misin??? (Y/n) : "),
                timeout=60  # 1 dakika içinde yanıt gelmezse timeout olacak
            )
            return yanit.strip().lower()
        except asyncio.TimeoutError:
            print(Fore.RED + "[⏳] Yanıt gelmedi, kontrol ediliyor...")
            # 1 dakika boyunca yanıt gelmezse n döndür
            return "n"  
        
    async def basla(self):
        ascii_text = pyfiglet.figlet_format("Zeysnepk") 
        print(Fore.MAGENTA + Style.BRIGHT + ascii_text)
        await asyncio.sleep(0.2)
        print(Fore.YELLOW + "[👻] Merhaba...")
        await asyncio.sleep(0.2)
        print(Fore.LIGHTWHITE_EX + "[👾] Başlamadan önceee...")
        await asyncio.sleep(0.2)
        print(Fore.CYAN + "[🫷] Lütfen sayfaların açılmasını bekleyiniz!!!")
        try:
            await self.kontenjan.basla(headless=True)
        except Exception as e:
            print(Fore.RED + f"[❌] Açılış hatası, e-okul sayfasına erişilemedi. Bilgilerinizi veya internetinizi kontrol ediniz: {str(e)}")
            await self.yeniden_basla()
            
        while True: 
            yanit = await self.yanit_bekle()
            if yanit == 'y':
                print(Fore.MAGENTA + f"[⏰] Lütfen e-devlet girişi ile bilgilerin alınmasını bekleyiniz..")
                await self.basvuru_ac()
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
                break
                
            elif yanit == 'n':
                print(Fore.LIGHTMAGENTA_EX + "[🎉] O zaman başlıyoruuz!!!")
                await asyncio.sleep(0.2)
                await self.kontrol_et()
                break
            
            else:
                print(Fore.RED + "[👿] Geçersiz giriş. Lütfen tekrar deneyin.")
                await asyncio.sleep(0.2)
                
    async def basvuru_ac(self):
        try:
            if self.basvuru_acik:
                await self.guvenli_bitir(self.basvuru, "Başvuru Sayfası")
            await self.basvuru.basla(headless=True)
            await asyncio.sleep(1)
            await self.basvuru.e_devlet_giris()
            print(Fore.GREEN + f"[🥳] Captcha çözüldü devam edebilirizzz")
            self.basvuru_acik = True
        except Exception as e:
            print(Fore.RED + f"[❌] Açılış hatası, başvuru sayfasına erişilemedi. Bilgilerinizi veya internetinizi kontrol ediniz: {str(e)}")
            await self.yeniden_basla("B")
                
    async def kontrol_et(self):
        while True:
            print(Fore.YELLOW + "[👀] Kontenjan Kontrolü...")
            await asyncio.sleep(0.2)
            try:
                kontenjan_sayisi = await self.kontenjan.kontenjan_kontrol()
            except Exception as e:
                # Sayfa, onay gününde girişlere kapalı olur
                print(Fore.RED + f"[❌] Hata, sayfa kapalı olabilir: {str(e)}")
                await asyncio.sleep(self.saniye)
                await self.yeniden_basla()
                continue
            await self.kontenjan.bitir()
            print(Fore.GREEN + f"[🔢] Kontenjan sayısı: {kontenjan_sayisi}")
            await asyncio.sleep(0.2)
            
            # Eğer kontenjan varsa basvuru yap
            if int(kontenjan_sayisi) > 0:
                print(Fore.CYAN + f"[⭐️] Kontenjan Bulundu Başvuruya Başlanıyor...")
                await self.basvuru_ac()
                await asyncio.sleep(1)
                await self.mail_gonder("Kontenjan Bulundu Başvuruya Başlanıyor...")
                mesaj = await self.basvuru.basvur()
                print(Fore.RED + f"[❓] Başvuru Sonucu: {mesaj}")
                await self.mail_gonder(mesaj)
                sys.exit(0)
            else:
                print(Fore.YELLOW + f"[⏰] {self.saniye} saniye sonra tekrar kontrol edilecek!")
            await asyncio.sleep(self.saniye)
            await self.yeniden_basla()
            
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
    
    async def internet_kontrol(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            return False
    
    async def guvenli_bitir(self, obj, ad):
        # Sayfaları güvenli bir şekilde kapatır hata verirse es geçer
        try:
            if hasattr(obj, "bitir"):
                await obj.bitir()
                print(Fore.GREEN + f"[✅] {ad} başarıyla kapatıldı.")
            else:
                print(Fore.YELLOW + f"[💤] {ad} zaten kapalıydı veya mevcut değil.")
        except Exception as e:
            print(Fore.RED + f"[❌] {ad} kapatılırken hata oluştu: {str(e)}")
    
    async def yeniden_basla(self, kontrol="K"):
        try:
            while not await self.internet_kontrol():
                print(Fore.YELLOW + "[⚠️] İnternet bağlantısı yok, bekleniyor...")
                await asyncio.sleep(60)
            # Sayfalar açıksa bitir
            if kontrol == "K":
                await self.guvenli_bitir(self.kontenjan, "Kontenjan Sayfası")
                await self.kontenjan.basla(headless=True)
            elif kontrol == "B":
                await self.guvenli_bitir(self.basvuru, "Başvuru Sayfası")
                await self.basvuru_ac()
            elif kontrol == "KB":
                await self.guvenli_bitir(self.kontenjan, "Kontenjan Sayfası")
                await self.guvenli_bitir(self.basvuru, "Başvuru Sayfası")
                await asyncio.gather(
                    self.kontenjan.basla(headless=True), 
                    self.basvuru.basla(headless=True)
                )  
                await asyncio.sleep(1)
                await self.basvuru.e_devlet_giris()
        except Exception as e:
            print(Fore.RED + f"[❌] Hata, yeniden başlatılamadı, bilgilerinizi kontrol ediniz: {str(e)}")
            
            await asyncio.sleep(self.saniye)
            await self.yeniden_basla()
            
    async def mail_gonder(self, mesaj):
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()  # Bağlantıyı güvenli hale getir
            server.login(self.mail_gonderen, self.sifre)
            
            # Mail içeriği
            msg = MIMEMultipart()
            msg["From"] = self.mail_gonderen
            msg["To"] = self.mail_alan
            msg["Subject"] = f"{self.bilgiler["okul"]} kontenjan bulundu!"
            msg.attach(MIMEText(f"{self.bilgiler["kimlik_no"]} numaralı öğrencinin nakil başvuru bilgilendirme:\n{mesaj}", "plain"))
            
            server.sendmail(self.mail_gonderen, self.mail_alan, msg.as_string())
            server.quit()
            print(Fore.GREEN + "[📧] Mail başarıyla gönderildi!")

        except Exception as e:
            print(Fore.RED + f"[❌] Hata, mail gönderilemedi: {str(e)}")
        
async def main_basla():
    await main.basla()
        
if __name__ == "__main__":
    # Bilgileri json dosyasından oku
    with open(json_dosyasi, 'r', encoding='utf-8') as file:
        json_bilgiler = json.load(file)
        
    main = Main(json_bilgiler)
    asyncio.run(main_basla())