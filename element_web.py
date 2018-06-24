import requests
from lxml import etree
import re
import json
from urllib import request
import pymysql

class ElementData(object):
	def __init__(self):
		self.base_url = 'http://data.xiguaji.com/Home'
		self.area_url = 'http://data.xiguaji.com/Rank/Area'
		self.industry_url = 'http://data.xiguaji.com/Rank/Industry'
		self.growth_url = 'http://data.xiguaji.com/Rank/Growth'
		self.map_url = 'http://data.xiguaji.com/Rank/Map'
		self.headers = {
			'Host':'data.xiguaji.com',
			'Connection':'keep-alive',
			'Accept':'*/*',
			'X-Requested-With':'XMLHttpRequest',
			'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
			'Referer':'http://data.xiguaji.com/Home',
			'Accept-Encoding':'gzip, deflate',
			'Accept-Language':'zh-CN,zh;q=0.9,en;q=0.8',
			'Cookie':'__lnkrntdmcvrd=-1; ASP.NET_SessionId=dxufr5k5xlozj0ikta0fbn5w; Qs_lvt_194035=1529403859%2C1529584602%2C1529627925%2C1529740284; Hm_lvt_91a409c98f787c8181d5bb8ee9c535ba=1529403862,1529584603,1529627925,1529740285; compareArray=[]; mediav=%7B%22eid%22%3A%22163230%22%2C%22ep%22%3A%22%22%2C%22vid%22%3A%226AD%3D%3DFO)%3D8%3C--eRH%25Aw)%22%2C%22ctn%22%3A%22%22%7D; xiguadata_advertise_survey=xiguadata_advertise_survey; XIGUADATA=UserId=4c35efb25bba133b&checksum=c70672d1eda5; Qs_pv_194035=4032044070017080000%2C2333450280516703700%2C4349570153806459400%2C1407376974546992000%2C3552817131943082000; Hm_lpvt_91a409c98f787c8181d5bb8ee9c535ba=1529747217',
		}
		self.db = pymysql.connect('192.168.12.139', 'alice', 'a11112222', 'image', charset='utf8')
		self.cursor = self.db.cursor()
		self.sql = 'INSERT INTO wxInfo(wxname, wxnumber) VALUES(%s, %s)'
		
	def getOnePage(self, url):
		response = requests.get(url=url, headers=self.headers)
		if response.status_code == requests.codes.ok:
			return response.text

	def parseCityUrl(self, html):
		html_obj = etree.HTML(html)
		link_list = html_obj.xpath('//ul[@class="city-type"]/li/a/@href')
		for link in link_list:
			yield link
	
	def parseResult(self, html):
		html_obj = etree.HTML(html)
		result_list = html_obj.xpath('//table[@class="table"]//td[2]/span')
		for result in result_list:
			wx_name = result.xpath('./span/text()')
			wx_number = result.xpath('./em/text()')
			yield wx_name, wx_number
	
	
	def areaData(self):
		html = self.getOnePage(self.map_url)
		pattern = re.compile('JSON.parse\(\'(.*)\'\)')
		res = pattern.search(html)
		list = (res.group(1))
		s = json.loads(list)
		for i in s:
			url = self.area_url + '?pid=' + str(i['id'])
			province_html = self.getOnePage(url)
			
			for city_url in self.parseCityUrl(province_html):
				city_url = city_url.lstrip('#')
				target_url = request.urljoin(self.base_url, city_url)
				
				html = self.getOnePage(target_url)
				for wx_name,wx_number in self.parseResult(html):
					print('+++++++++++++++',wx_name, wx_number)
					if wx_name is None or wx_number is None:
						continue
					self.dbInsert((wx_number, wx_name))

	def growthData(self):
		html = self.getOnePage(self.growth_url)
		date_list = self.parseCityUrl(html)
		for date_url in date_list:
			date_url = date_url.lstrip('#')
			target_url = request.urljoin(self.base_url, date_url)
			target_html = self.getOnePage(target_url)
			for wx_name,wx_number in self.parseResult(target_html):
				if wx_name is None or wx_number is None:
					continue
				self.dbInsert((wx_number,wx_name))
	
	
	def industryDate(self):
		html = self.getOnePage(self.industry_url)
		html_obj = etree.HTML(html)
		date_list = html_obj.xpath('//select[@id="IndustryRankDate"]/option/@value')
		for title in self.parseCityUrl(html):
			title_url = title.lstrip('#')
			target_url = request.urljoin(self.base_url, title_url)
			for date in date_list:
				final_url = target_url + '&date=' + date
				final_html = self.getOnePage(final_url)
				for wx_name, wx_number in self.parseResult(final_html):
					if wx_name is None or wx_number is None:
						continue
					self.dbInsert((wx_name, wx_number))
			


	def dbInsert(self, item):
		try:
			self.cursor.execute(self.sql, item)
			self.db.commit()
		except:
			self.db.rollback()
			print("数据已存在，跳过当前数据")
			
if __name__ == '__main__':
	a = ElementData()
	a.industryDate()
	