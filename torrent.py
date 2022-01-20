from datetime import datetime
import hashlib 
import struct
import random
import requests

import bencoding
import utils

class File:
  def __init__(self, filepath):
    self.filepath = filepath
    f = open(filepath, "rb")
    self.raw_torrent = f.read()
    f.close()
    self.torrent_header = bencoding.decode(self.raw_torrent)
    self.announce = self.torrent_header[b"announce"].decode("utf-8")
    torrent_info = self.torrent_header[b"info"]
    m = hashlib.sha1()
    m.update(bencoding.encode(torrent_info))
    self.file_hash = m.digest()

  @property
  def total_size(self):
    size = 0
    torrent_info = self.torrent_header[b"info"]
    if b"files" in torrent_info:
      # Multiple File Mode
      for file_info in torrent_info[b"files"]:
        size += file_info[b"length"]
    else:
      # Single File Mode
      size = torrent_info[b"length"]

    return size

  def __str__(self):
    announce = self.torrent_header[b"announce"].decode("utf-8")
    result = "Announce: %s\n" % announce
        
    if b"creation date" in self.torrent_header:
      creation_date = self.torrent_header[b"creation date"]
      creation_date = datetime.fromtimestamp(creation_date)
      result += "Date: %s\n" % creation_date.strftime("%Y/%m/%d %H:%M:%S")

    if b"created by" in self.torrent_header:
      created_by = self.torrent_header[b"created by"].decode("utf-8")
      result += "Created by: %s\n" % created_by

    if b"encoding" in self.torrent_header:
      encoding = self.torrent_header[b"encoding"].decode("utf-8")
      result += "Encoding:   %s\n" % encoding
        
    torrent_info = self.torrent_header[b"info"]
    piece_len = torrent_info[b"piece length"]
    result += "Piece len: %s\n" % utils.sizeof_fmt(piece_len)
    pieces = len(torrent_info[b"pieces"]) / 20
    result += "Pieces: %d\n" % pieces

    torrent_name = torrent_info[b"name"].decode("utf-8")
    result += "Name: %s\n" % torrent_name
    piece_len = torrent_info[b"piece length"]

    # if b"files" in torrent_info:
    #   # Multiple File Mode
    #   result += "Files:\n"
    #   for file_info in torrent_info[b"files"]:
    #     fullpath = "/".join([x.decode("utf-8") for x in file_info[b"path"]])
    #     result += "  '%s' (%s)\n" % (fullpath, 
    #         utils.sizeof_fmt(file_info[b"length"]))
    # else:
    #   # Single File Mode
    #   result += "Length: %s\n" % utils.sizeof_fmt(torrent_info[b"length"])
    #   if b"md5sum" in torrent_info:
    #     result += "Md5: %s\n" % torrent_info[b"md5sum"]

    return result


class Seeder:
  HTTP_HEADERS = {
    "Accept-Encoding": "gzip",
    "User-Agent": "Transmission/2.94"
  }

  def __init__(self, torrent):
    self.torrent = torrent
    self.peer_id = "-TR2940-" + utils.random_id(12)
    self.download_key = utils.random_id(12)
    self.port = 62567

  def load_peers(self):
    tracker_url = self.torrent.announce
    http_params = {
      "info_hash": self.torrent.file_hash, 
      "peer_id": self.peer_id.encode("ascii"),
      "port": self.port,
      "uploaded": 0,
      "downloaded": 0,
      "left": 0, # 假下载模式:self.torrent.total_size 假上传模式:0
      "event": "started",
      "key": self.download_key,
      "compact": 1,
      "numwant": 200,
      "supportcrypto": 1,
      "no_peer_id": 1
    }
    req = requests.get(tracker_url, params=http_params, 
        headers=self.HTTP_HEADERS)
    self.info = bencoding.decode(req.content)

  def stop(self):
    tracker_url = self.torrent.announce
    http_params = {
      "info_hash": self.torrent.file_hash, 
      "peer_id": self.peer_id.encode("ascii"),
      "port": self.port,
      "uploaded": 0,
      "downloaded": 0,
      "left": 0, # 假下载模式:self.torrent.total_size 假上传模式:0
      "event": "stopped",
      "key": self.download_key,
      "compact": 1,
      "numwant": 200,
      "supportcrypto": 1,
      "no_peer_id": 1
    }
    req = requests.get(tracker_url, params=http_params, 
        headers=self.HTTP_HEADERS)

  def upload(self):
    tracker_url = self.torrent.announce
    http_params = {
      "info_hash": self.torrent.file_hash, 
      "peer_id": self.peer_id.encode("ascii"),
      "port": self.port,
      "uploaded": 0, # 如果要作弊上传速度
      "downloaded": 0,
      "left": 0, # 假下载模式:self.torrent.total_size 假上传模式:0
      "key": self.download_key,
      "compact": 1,
      "numwant": 0,
      "supportcrypto": 1,
      "no_peer_id": 1
    }
    requests.get(tracker_url, params=http_params, headers=self.HTTP_HEADERS)

  @property
  def peers(self):
    result = []
    peers = self.info[b"peers"]
    for i in range(len(peers)//6):
      ip = peers[i:i+4]
      ip = '.'.join("%d" %x for x in ip)
      port = peers[i+4:i+6]
      port = struct.unpack(">H", port)[0]
      result.append("%s:%d\n" % (ip, port))
    return result

  def __str__(self):
    result  = "Peer ID: %s\n" % self.peer_id
    result += "Key: %s\n" % self.download_key
    result += "Port: %d\n" % self.port
    return result
