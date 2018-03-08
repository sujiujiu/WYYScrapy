# -*-coding:utf-8-*-
from __future__ import absolute_import
import re
import sys
import requests

import scrapy
from scrapy.http import Request
from WangYiYun.items import WYYArtistItem, WYYAlbumListItem, WYYAlbumItem, WYYSongItem
from CommentCrawl import CommentCrawlClass
# from scrapy.selector import Selector
# from scrapy.spiders import CrawlSpider, Rule
# from scrapy.linkextractors import LinkExtractor



class WangYiYunCrawl(scrapy.Spider):
    name = 'WangYiYun'
    allowed_domains = ['music.163.com']
    # start_urls = 'http://music.163.com/discover/artist/cat?id={gid}&initial={initial}'
    group_ids = (1001, 1002, 1003, 2001, 2002, 2003, 6001, 6002, 6003, 7001, 7002, 7003, 4001, 4002, 4003)
    initials = [i for i in range(65,91)] + [0]
    headers = {
            "Referer":"http://music.163.com",
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3067.6 Safari/537.36",
        }

    def start_requests(self):
        for gid in self.group_ids:
            for initial in self.initials:
                url = 'http://music.163.com/discover/artist/cat?id={gid}&initial={initial}'.\
                        format(gid=gid, initial=initial)
                yield scrapy.Request(url=url, headers=self.headers, method='GET', callback=self.parse)

    def parse(self,response):
        '''从http://music.163.com/discover/artist/cat?id={gid}&initial={initial}抓取所有的歌手页
        '''
        lis = response.selector.xpath('//ul[@id="m-artist-box"]/li')
        for li in lis:
            post_urls = li.xpath('//a[@class="nm nm-icn f-thide s-fc0"]/@href').extract()
            for post_url in post_urls:
                item = WYYArtistItem()
                p_url = post_url.lstrip()
                album_url = p_url.split('?')
                item['artist_id'] = int(re.compile(r'\d+').findall(p_url)[0])
                item['aritst_url'] = 'http://music.163.com' + p_url
                item['album_url'] = 'http://music.163.com' + album_url[0] + '/album?' + album_url[1]
                item['artist_name'] = li.xpath('//a[@class="nm nm-icn f-thide s-fc0"]/text()').extract()[0]
                yield scrapy.Request(url=item['album_url'], headers=self.headers, method='GET', callback=self.parse_album_list)

    def get_album_list_page(self,response):
        '''判断http://music.163.com/artist/album?id=xx页的专辑有多少页，如果标签不在，则返回1
        '''
        page = response.selector.xpath('//a[@class="zpgi"]/text()').extract()
        if page:
            page = int(page[-1])
        else:
            page = 1
        return page

    def parse_album_list(self,response):
        '''歌手的所有专辑
        '''
        item = WYYAlbumListItem()
        singer_id = response.url[37:]
        item['album_id'] = singer_id
        item['album_url'] = response.url
        page_count = self.get_album_list_page(response)
        album_list = self.get_artist_album_info(singer_id,page_count)
        item['album_list_info'] = album_list
        for albums in album_list:
            hotAlbums = albums['hotAlbums']
            for hot_album in hotAlbums:
                album_id = hot_album['id']
                album_url = 'http://music.163.com/album?id=' + str(album_id)
                yield scrapy.Request(url=album_url, headers=self.headers, method='GET', callback=self.parse_album)

    def parse_album(self,response):
        '''获取每张专辑里的所有歌曲列表
        '''
        item = WYYAlbumItem()
        album_id = response.url[30:]
        comment_url = 'http://music.163.com/weapi/v1/resource/comments/R_AL_3_%s?csrf_token=' % album_id
        item['album_id'] = album_id
        item['album_url'] = response.url

        album_info = self.get_album_info(album_id)
        album_comment_count = album_info['album']['info']['commentCount'] 
        item['album_info'] = album_info
        item['album_comment_count'] = album_comment_count
        item['album_comment_info'] = CommentCrawlClass(comment_url).get_album_comment(album_comment_count)

        songs = album_info['album']['songs']
        if songs:
            for song in songs:
                song_id = song['id']
                song_url = 'http://music.163.com/song?id=' + str(song_id)
                yield scrapy.Request(url=song_url, headers=self.headers, method='GET', callback=self.parse_song)

    def parse_song(self,response):
        item = WYYSongItem()
        song_id = response.url[29:]
        item['song_id'] = song_id
        comment_url = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_%s?csrf_token=' % song_id
        item['song_url'] = response.url
        item['lyric'] = self.get_lyric(song_id)
        item['song_info'] = self.get_song_info(song_id)
        item['song_comments'] = CommentCrawlClass(comment_url).get_song_comment()
        yield item
    
    def get_req(self,url,params=None):
        try:
            req = requests.get(url,headers=self.headers,params=params)
            return req
        except Exception,e:
            with open('C:\\Users\\Administrator\\Desktop\\jijian-intern\\WangYiYun\\WangYiYun\\WangYiYun\\error_url.txt','a+') as f:
                f.write(url+'\n')
            print req.url,e
            return None

    def get_artist_album_info(self,singer_id,page_count):
        '''每个歌手的所有专辑信息
        '''
        album_list = []
        albums_url = 'http://music.163.com/api/artist/albums/%s' % singer_id
        for offset in range(0,page_count):
            params = {
                'id':singer_id,
                'offset':offset*12,
                'total':'true',
                'limit':12
            }
            req = self.get_req(albums_url,params=params)
            data = req.json()
            album_list.append(data)
        return album_list

    def get_album_info(self,album_id):
        '''专辑信息
        '''
        songs_url = 'http://music.163.com/api/album/%s?ext=true&id=%s&offset=0&total=true' % (album_id,album_id)
        req = self.get_req(songs_url)
        if req.status_code == 200:
            return req.json()

    def get_song_info(self,song_id):
        '''每首歌的歌曲信息
        '''
        # param = urlencode({'id':%s,'ids':[%s]}) % (song_id,song_id)
        song_url = 'http://music.163.com/api/song/detail/?id=%s&ids=[%s]' % (song_id,song_id)
        req = self.get_req(song_url)
        if req.status_code == 200:
            return req.json()

    def get_lyric(self, song_id):
        '''歌词信息
        '''
        lyric_url = 'http://music.163.com/api/song/lyric?os=pc&id=%s&lv=-1&kv=-1&tv=-1' % song_id
        req = self.get_req(lyric_url)
        if req.status_code == 200:
            return req.json()
        else:
            return 'None'
