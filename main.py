import json
import asyncio
from playwright.async_api import async_playwright
import sys
import easyocr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket

dosya = "bilgiler.json"
kontenjan_url = "https://e-okul.meb.gov.tr/OrtaOgretim/OKL/OOK06011.aspx"
nakil_url = "https://www.turkiye.gov.tr/meb-ogrenci-nakil-islemi"

class Nakil():
    def __init__(self, bilgiler):
        self.bilgiler = bilgiler
        
        self.playwright = None
        self.browser = None
        self.page = None
        
        # Kontenjan Sayfası CSS
        self.tc_input = 'input[name="txtTcKimlikNo"]'
        self.okul_no_input = 'input[name="txtOkulNo"]'
        self.il_dropdown = '#ddlIl_K_chzn > a'
        self.il_sec = '#ddlIl_K_chzn > div > ul > li'
        self.ilce_dropdown = '#ddlIlce_chzn > a'
        self.ilce_sec = '#ddlIlce_chzn > div > ul > li'
        self.kurum_turu_dropdown = '#ddlKurumTuru'
        self.kayit_alani_dropdown = '#ddlKayitAlani'
        self.okul_dropdown = '#ddlOkul_chzn > a'
        self.okul_sec = '#ddlOkul_chzn > div > ul > li'
        self.listele_buton = 'input[value="Listele"]'
        self.sinif = int(self.bilgiler["sinif"]) - 6
        self.sinif_kontenjan = f"#dgListe > tbody > tr:nth-child(2) > td:nth-child({self.sinif})"
        
        # Nakil Sayfası CSS
        self.dogrula_buton = '#contentStart > div > div.authAction > a'
        self.tc_input2 = 'input[name="tridField"]'
        self.sifre_input = 'input[name="egpField"]'
        self.giris_buton = 'button[name="submitButton"]'
        self.captcha_img = '#loginForm > fieldset > div:nth-child(4) > div > img'
        self.captcha_input = 'input[name="captchaField"]'
        self.hata_metin = '#loginForm > fieldset > div.form-row.required.form-error > div > span:nth-child(5)'   
        self.baglan_buton = '#contentStart > div.resultContainer > div > table > tbody > tr > td:nth-child(3) > a'
        self.neden_input = '#ddlNakilNedeni'
        self.tur_input = '#ddlNakilTurleri'
        self.alan_input = '#ddlNakilAlanlari'
        self.dal_input = '#ddlNakilDali'
        self.il_input = '#ddlBasvuruIli'
        self.okul_input = '#ddlBasvuruKurum'
        self.dil_input = '#ddlOkulYabanciDil'
        self.tik_at = 'input[name="chkNakil"]'
        self.kaydet_buton = 'input[name="btnKaydet"]'
        
    async def browser_ac(self):
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            
    async def sayfa_ac(self, url):
        self.page = await self.browser.new_page()
        await self.page.goto(url, wait_until="networkidle", timeout=10000)
        self.page.on("dialog", lambda dialog: dialog.accept())
        
    async def sayfa_kapa(self):
        if self.page:
            await self.page.close()
            self.page = None
            
    async def browser_kapa(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
            
    async def sayfa_yenile(self):
        if self.page:
            await self.page.reload()
            
    async def doldur(self, secim, deger):
        await self.page.wait_for_selector(secim, state="visible", timeout=5000)
        await self.page.fill(secim, deger)
        await self.page.wait_for_timeout(100)
        
    async def tikla_filter(self, secim_dropdown, secim, deger):
        await self.page.wait_for_selector(secim_dropdown, state="visible", timeout=5000)
        await self.page.locator(secim_dropdown).click()
        await self.page.wait_for_selector(secim, state="visible", timeout=5000)
        await self.page.locator(secim).filter(has_text=deger).click()
        await self.page.wait_for_timeout(100)
                   
    async def tikla_option(self, secim_dropdown, deger):
        await self.page.wait_for_selector(secim_dropdown, state="attached", timeout=10000)
        await self.page.locator(secim_dropdown).click()
        await self.page.select_option(secim_dropdown, label=deger)
        await self.page.wait_for_timeout(100)
            
    async def kontenjan_kontrol(self, okul):
        await self.doldur(self.tc_input, self.bilgiler["kimlik_no"])
        await self.doldur(self.okul_no_input, self.bilgiler["okul_no"])
        await self.tikla_filter(self.il_dropdown, self.il_sec, self.bilgiler["il"])
        await self.tikla_filter(self.ilce_dropdown, self.ilce_sec, self.bilgiler["ilce"])
        await self.tikla_option(self.kurum_turu_dropdown, self.bilgiler["kurum_turu"])
        await self.tikla_option(self.kayit_alani_dropdown, self.bilgiler["kayit_alani"])
        await self.tikla_filter(self.okul_dropdown, self.okul_sec, okul)
        await self.page.locator(self.listele_buton).click()
        await self.page.wait_for_timeout(100)
        kontenjan = await self.page.locator(self.sinif_kontenjan).inner_text()
        return int(kontenjan)
    
    def captcha_coz(self, image_path):
        try:
            reader = easyocr.Reader(['en']) 
            captcha_text = reader.readtext(image_path, detail=0)

            return captcha_text[0]
        except Exception as e:
            print(f"Captcha okunamadı: {e}")
            return "bilmiyorum"
    
    async def e_devlet_giris(self):
        self.dongu = True
        await self.page.locator(self.dogrula_buton).click()     
        await self.page.wait_for_timeout(1000)
        await self.doldur(self.tc_input2, self.bilgiler["edevlet_no"])  
        await self.doldur(self.sifre_input, self.bilgiler["edevlet_sifre"])
        await self.page.locator(self.giris_buton).click()
        await self.page.wait_for_timeout(1000)
        
        # Captcha çözülene kadar tekrar tekrar dene
        while self.dongu:
            captcha = await self.page.locator(self.captcha_img).is_visible()
            if captcha:
                print("captcha var")
                captcha_path = "captcha.png"
                await self.page.locator(self.captcha_img).screenshot(path=captcha_path)
                captcha_text = self.captcha_coz(captcha_path)
                
                print(f"Okunan Captcha Kodu: {captcha_text}")
                
                await self.page.fill(self.captcha_input, captcha_text)
                await self.page.fill(self.sifre_input, self.bilgiler["edevlet_sifre"])
                await self.page.locator(self.giris_buton).click()
                
                # Hata mesajı varsa captcha çözülememiş tekrar döngüde
                hata_metin = await self.page.locator(self.hata_metin).is_visible()
                
                # Hata mesajı yoksa döngüden çık
                if not hata_metin:
                        self.dongu = False

            # Captcha yoksa döngüden çık
            else: 
                print("captcha yok")
                break
        # Butonun sayfada görünmesini bekle
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_selector(self.baglan_buton, state="attached", timeout=5000)
        # Butona bastıktan sonra yeni açılan pop-up bilgisi
        async with self.page.expect_popup(timeout=60000) as popup_info:
            await self.page.locator(self.baglan_buton).click() 

        # Yeni açılan sayfaya geç
        self.page = await popup_info.value
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_load_state("domcontentloaded")
        
        # Sayfaya gelen mesajlar için oto kabul et
        self.page.on("dialog", lambda dialog: dialog.accept())
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(1000)
    
    async def basvuru_yap(self, okul):
        await self.tikla_option(self.neden_input, self.bilgiler["nakil_nedeni"])
        await self.tikla_option(self.tur_input, self.bilgiler["gidilecek_tur"])
        await self.tikla_option(self.alan_input, self.bilgiler["gidilecek_alan"])
        await self.tikla_option(self.dal_input, self.bilgiler["gidilecek_dal"])
        await self.tikla_option(self.il_input, self.bilgiler["il"])
        await self.tikla_option(self.okul_input, okul)
        await self.tikla_option(self.dil_input, self.bilgiler["yabanci_dil"])
        await self.page.locator(self.tik_at).click()
        await self.page.locator(self.kaydet_buton).click()
        await self.page.wait_for_timeout(100)
        return await self.page.locator('#lblHata').inner_text()
        
def mail_gonder(okul, mesaj):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls() 
        server.login(bilgiler["mail_gonderen"], bilgiler["mail_app_sifre"])
        msg = MIMEMultipart()
        msg["From"] = bilgiler["mail_gonderen"]
        msg["To"] = bilgiler["mail_alan"]
        msg["Subject"] = f"{okul} kontenjan bulundu!"
        msg.attach(MIMEText(f"{bilgiler["kimlik_no"]} numaralı öğrencinin nakil başvuru bilgilendirme:\n{mesaj}", "plain"))
        server.sendmail(bilgiler["mail_gonderen"], bilgiler["mail_alan"], msg.as_string())
        server.quit()
        print("Mail başarıyla gönderildi!")
    except Exception as e:
        print(f"Mail gönderilirken hata oluştu: {e}")
    
def internet_kontrol():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        print("İnternet bağlantısı yok")
        return False
        
    
async def basla():
    try:
        print("Browser açılıyor...")
        await nakil.browser_ac()
        print("Kontenjan sayfası açılıyor...")
        while True:
            await nakil.sayfa_ac(kontenjan_url)
            for okul in bilgiler["okul"]:
                kontenjan = await nakil.kontenjan_kontrol(okul)
                print(f"{okul} okulunun kontenjan sayısı: {kontenjan}")
                await asyncio.sleep(1)
                if( kontenjan > 0 ):
                    print(f"{okul} için kontenjan bulundu maili gönderiliyor...")
                    mail_gonder(okul, "Kontenjana Başlanıyor")
                    print("Kontenjan sayfası kapanıyor...")
                    await nakil.sayfa_kapa()
                    print("E-Devlet sayfası açılıyor...")
                    await nakil.sayfa_ac(nakil_url)
                    await asyncio.sleep(1)
                    await nakil.e_devlet_giris()
                    await asyncio.sleep(1)
                    print("Başvuru yapılıyor...")
                    nakil_okul_in = bilgiler["okul"].index(okul)
                    nakil_okul = bilgiler["gidilecek_okul"].pop(nakil_okul_in)
                    mesaj = await nakil.basvuru_yap(nakil_okul)
                    print(f"Başvuru Sonucu: {mesaj}")
                    mail_gonder(okul, "Kontenjana Başlanıyor")
                    await asyncio.sleep(1)
                    print("Başvuru sayfası kapanıyor...")
                    await nakil.sayfa_kapa()
                    print("Browser kapatılıyor...")
                    await nakil.browser_kapa()
                    sys.exit(0)    
                print("Kontenjan sayfası tekrar yükleniyor...")
                await nakil.sayfa_yenile()
            await nakil.sayfa_kapa()
            await asyncio.sleep(int(bilgiler["saniye"])) 
    except Exception as e:
        if not internet_kontrol():
            print("Bağlantı yok, tekrar denenecek...")
        print(f"Hata: {e}")
        await asyncio.sleep(10)
        await basla()
        
        
with open(dosya, 'r', encoding='utf-8') as file:
    bilgiler = json.load(file)
        
nakil = Nakil(bilgiler)
asyncio.run(basla())
