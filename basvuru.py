import json
import asyncio
from playwright.async_api import async_playwright
import easyocr

class Basvuru():
    def __init__(self, bilgiler):
        self.bilgiler = bilgiler
        self.dongu = True
        self.edevlet_url = "https://www.turkiye.gov.tr/meb-ogrenci-nakil-islemi"
        
        self.dogrula_buton = '#contentStart > div > div.authAction > a'
        
        self.tc_input = 'input[name="tridField"]'
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
        
        self.browser = None
        self.page = None
        self.playwright = None
        
    async def basla(self, headless=False):
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=headless)
            self.page = await self.browser.new_page()
            await self.page.goto(self.edevlet_url, wait_until="networkidle")
            self.page.on("dialog", lambda dialog: dialog.accept())
            await self.page.wait_for_timeout(100)
            
    async def bitir(self):
        if self.browser:
            if self.basvuru_sayfasi:
                await self.basvuru_sayfasi.close()
            await self.page.wait_for_timeout(100)
            await self.browser.close()
            await self.playwright.stop()
            self.browser = None
            self.page = None   
            
    async def doldur(self, secim, deger):
        await self.page.wait_for_selector(secim, state="visible", timeout=5000)
        await self.page.fill(secim, deger)
        await self.page.wait_for_timeout(100)
                   
    async def tikla_option(self, secim_dropdown, deger):
        await self.basvuru_sayfasi.wait_for_selector(secim_dropdown, state="visible", timeout=5000)
        await self.basvuru_sayfasi.locator(secim_dropdown).click()
        await self.basvuru_sayfasi.select_option(secim_dropdown, label=deger)
        await self.basvuru_sayfasi.wait_for_timeout(100)
        
    async def nakil_nedeni_gir(self):
        await self.tikla_option(self.neden_input, self.bilgiler["nakil_nedeni"])
        
    async def tur_gir(self):
        await self.tikla_option(self.tur_input, self.bilgiler["gidilecek_tur"])
        
    async def alan_gir(self):
        await self.tikla_option(self.alan_input, self.bilgiler["gidilecek_alan"])
        
    async def dal_gir(self):
        await self.tikla_option(self.dal_input, self.bilgiler["gidilecek_dal"])
        
    async def il_gir(self):
        await self.tikla_option(self.il_input, self.bilgiler["il"])
        
    async def okul_gir(self):
        await self.tikla_option(self.okul_input, self.bilgiler["gidilecek_okul"])
        
    async def dil_gir(self):
        await self.tikla_option(self.dil_input, self.bilgiler["yabanci_dil"])
        
    async def tum_bilgileri_gir(self):
        await self.nakil_nedeni_gir()
        await self.tur_gir()
        await self.alan_gir()
        await self.dal_gir()
        await self.il_gir()
        await self.okul_gir()
        await self.dil_gir()
        
    async def basvuru_yap(self):
        await self.tum_bilgileri_gir()
        await self.basvuru_sayfasi.locator(self.tik_at).click()
        await self.basvuru_sayfasi.locator(self.kaydet_buton).click()
        await self.basvuru_sayfasi.wait_for_timeout(100)
        await asyncio.sleep(5)
        
    def captcha_coz(self, image_path):
        try:
            reader = easyocr.Reader(['en']) 
            captcha_text = reader.readtext(image_path, detail=0)

            return captcha_text[0]
        except Exception as e:
            print(f"Captcha okunamadı: {e}")
            return "bilmiyorum"
        
    async def e_devlet_giris(self):
        await self.page.locator(self.dogrula_buton).click()     
        await self.page.wait_for_timeout(1000)
        await self.doldur(self.tc_input, self.bilgiler["edevlet_no"])  
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
        await self.page.wait_for_selector(self.baglan_buton, state="visible", timeout=5000)
        # Butona bastıktan sonra yeni açılan pop-up bilgisi
        async with self.page.expect_popup(timeout=60000) as popup_info:
            await self.page.locator(self.baglan_buton).click() 

        # Yeni açılan sayfaya geç
        self.basvuru_sayfasi = await popup_info.value
        await self.basvuru_sayfasi.wait_for_load_state("networkidle")
        await self.basvuru_sayfasi.wait_for_load_state("domcontentloaded")
        
        # Sayfaya gelen mesajlar için oto kabul et
        self.basvuru_sayfasi.on("dialog", lambda dialog: dialog.accept())
        await self.basvuru_sayfasi.wait_for_timeout(1000)
        
    async def mesaj(self):
        return await self.basvuru_sayfasi.locator('#lblHata').inner_text()
    
    async def secenekleri_dondur(self, name):
        await self.basvuru_sayfasi.wait_for_selector(name, state="attached", timeout=5000)
        secenekler = await self.basvuru_sayfasi.locator(name).all_inner_texts()
        await self.basvuru_sayfasi.wait_for_timeout(100)
        return secenekler
    
    async def nedenleri_listele(self):
        return await self.secenekleri_dondur('#ddlNakilNedeni > option')
    
    async def turleri_listele(self):
        return await self.secenekleri_dondur('#ddlNakilTurleri > option')
    
    async def alanlari_listele(self):
        await self.tur_gir()
        return await self.secenekleri_dondur('#ddlNakilAlanlari > option')
    
    async def dallari_listele(self):
        await self.tur_gir()
        await self.alan_gir()
        return await self.secenekleri_dondur('#ddlNakilDali > option')
    
    async def illeri_listele(self):
        return await self.secenekleri_dondur('#ddlBasvuruIli > option')
    
    async def okullari_listele(self):
        await self.tur_gir()
        await self.alan_gir()
        await self.dal_gir()
        await self.il_gir()
        return await self.secenekleri_dondur('#ddlBasvuruKurum > option')
    
    async def dilleri_listele(self):
        await self.tur_gir()
        await self.alan_gir()
        await self.dal_gir()
        await self.il_gir()
        await self.okul_gir()
        return await self.secenekleri_dondur('#ddlOkulYabanciDil > option')
    
    async def basvur(self):
        await basvuru.e_devlet_giris()
        await basvuru.basvuru_yap()
        mesaj = await basvuru.mesaj()
        await basvuru.bitir()
        return mesaj
    
    
async def main_basla(basvuru):
        await basvuru.basla()
        await basvuru.e_devlet_giris()
        await asyncio.sleep(2)
        #await basvuru.tum_bilgileri_gir()
        print(await basvuru.nedenleri_listele())
        await basvuru.bitir()
        """
        mesaj = await basvuru.basvur()
        print("Başvuru Sonucu: ", mesaj)
    except Exception as e:
        print("Başvuru Yapılamadı: ", str(e))"""
    
if __name__ == "__main__":
    with open("config.json", 'r', encoding='utf-8') as file:
        json_bilgiler = json.load(file)
    basvuru = Basvuru(json_bilgiler)
    asyncio.run(main_basla(basvuru))