# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WYYArtistItem(scrapy.Item):
    '''获取所有歌手url
    '''
    _id = scrapy.Field()
    artist_id = scrapy.Field()
    artist_name = scrapy.Field()
    aritst_url = scrapy.Field()
    album_url = scrapy.Field()


class WYYAlbumListItem(scrapy.Item):
    '''歌手的所有专辑
    '''
    _id = scrapy.Field()
    album_id = scrapy.Field()
    album_url = scrapy.Field()
    album_list_info = scrapy.Field()


class WYYAlbumItem(scrapy.Item):
    '''专辑的所有歌列表
    '''
    _id = scrapy.Field()
    album_id = scrapy.Field()
    album_url = scrapy.Field()
    album_info = scrapy.Field()
    album_comment_count = scrapy.Field()
    album_comment_info = scrapy.Field()

class WYYSongItem(scrapy.Item):
    '''每首歌信息
    '''
    _id = scrapy.Field()
    song_id = scrapy.Field()
    song_url = scrapy.Field()
    lyric = scrapy.Field()
    song_info = scrapy.Field()
    song_comments = scrapy.Field()
    song_comment_count = scrapy.Field()




