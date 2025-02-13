import json
import asyncio
from playwright.async_api import async_playwright

class Kontenjan():
    def __init__(self, bilgiler):
        self.bilgiler = bilgiler
        self.url = "https://e-okul.meb.gov.tr/OrtaOgretim/OKL/OOK06011.aspx"
        
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
        
        self.browser = None
        self.page = None
        self.playwright = None
        
    async def basla(self, headless=False):
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=headless)
            self.page = await self.browser.new_page()
            await self.page.goto(self.url, wait_until="networkidle")
            print("Kontenjan tamam")
            await self.page.wait_for_timeout(100)
            
    async def bitir(self):
        if self.browser:
            await self.page.wait_for_timeout(100)
            await self.browser.close()
            await self.playwright.stop()
            self.browser = None
            self.page = None   
            
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
        await self.page.wait_for_selector(secim_dropdown, state="visible", timeout=5000)
        await self.page.locator(secim_dropdown).click()
        await self.page.select_option(secim_dropdown, label=deger)
        await self.page.wait_for_timeout(100)
        
    async def tc_gir(self):
        await self.doldur(self.tc_input, self.bilgiler["kimlik_no"])
        
    async def okul_no_gir(self):
        await self.doldur(self.okul_no_input, self.bilgiler["okul_no"])
        
    async def il_gir(self):
        await self.tikla_filter(self.il_dropdown, self.il_sec, self.bilgiler["il"])
        
    async def ilce_gir(self):
        await self.tikla_filter(self.ilce_dropdown, self.ilce_sec, self.bilgiler["ilce"])
        
    async def kurum_turu_gir(self):
        await self.tikla_option(self.kurum_turu_dropdown, self.bilgiler["kurum_turu"])
        
    async def kayit_alani_gir(self):
        await self.tikla_option(self.kayit_alani_dropdown, self.bilgiler["kayit_alani"])
        
    async def okul_gir(self):
        await self.tikla_filter(self.okul_dropdown, self.okul_sec, self.bilgiler["okul"])
        
    async def tum_bilgileri_gir(self):
        await self.tc_gir()
        await self.okul_no_gir()
        await self.il_gir()
        await self.ilce_gir()
        await self.kurum_turu_gir()
        await self.kayit_alani_gir()
        await self.okul_gir()
        
    async def kontenjan_kontrol(self):
        await self.tum_bilgileri_gir()
        await self.page.locator(self.listele_buton).click()
        await self.page.wait_for_timeout(100)
        kontenjan = await self.page.locator(self.sinif_kontenjan).inner_text()
        return int(kontenjan)
    
    async def secenekleri_dondur(self, name):
        #await self.page.wait_for_selector(name, state="visible", timeout=5000)
        secenekler = await self.page.locator(name).all_inner_texts()
        await self.page.wait_for_timeout(100)
        return secenekler
        
    async def illeri_listele(self):
        return await self.secenekleri_dondur('#ddlIl_K_chzn > div > ul > li')
    
    async def ilceleri_listele(self):
        await self.il_gir()
        return await self.secenekleri_dondur('#ddlIlce_chzn > div > ul > li')
    
    async def kurum_turleri_listele(self):
        await self.il_gir()
        await self.ilce_gir()
        return await self.secenekleri_dondur('#ddlKurumTuru > option')
    
    async def kayit_alanlari_listele(self):
        return await self.secenekleri_dondur('#ddlKayitAlani > option')
    
    async def okullari_listele(self):
        await self.tc_gir()
        await self.okul_no_gir()
        await self.il_gir()
        await self.ilce_gir()
        await self.kurum_turu_gir()
        await self.kayit_alani_gir()
        return await self.secenekleri_dondur('#ddlOkul_chzn > div > ul > li')
    
    async def okul_sayisi(self):
        await self.tum_bilgileri_gir()
        return await self.page.locator('#lblOkulSayisi').inner_text()
    
async def main_basla(kontenjan):
        await kontenjan.basla()
        #print("Kontenjan: ", await kontenjan.kontenjan_kontrol())
        print(await kontenjan.okullari_listele())
        print("Okul Sayısı: ", await kontenjan.okul_sayisi())
        await kontenjan.bitir()
        """
    except Exception as e:
        print("Okul bulunamadı: ", str(e))
        await kontenjan.bitir()"""
    
if __name__ == "__main__":
    with open("bilgiler.json", 'r', encoding='utf-8') as file:
        json_bilgiler = json.load(file)
    kontenjan = Kontenjan(json_bilgiler)
    asyncio.run(main_basla(kontenjan))