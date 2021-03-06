#_*_coding:utf-8_*_
#linux:yum install python-boto
#windows:pip install boto
import boto
import boto.s3.connection
from boto.s3.connection import Key
#pip install filechunkio
from filechunkio import  FileChunkIO
import math
import  threading
import os
import Queue
class Chunk(object):
    num = 0
    offset = 0
    len = 0
    def __init__(self,n,o,l):
        self.num=n
        self.offset=o
        self.length=l



class CONNECTION(object):
    def __init__(self,access_key,secret_key,ip,port,is_secure=False,chrunksize=8<<20,bucket_limit=10): #chunksize最小8M否则上传过程会报错
        self.conn=boto.connect_s3(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        host=ip,port=port,
        is_secure=is_secure,
        calling_format=boto.s3.connection.OrdinaryCallingFormat()
        )
        self.chrunksize=chrunksize
        self.port=port
        self.bucket_limit=bucket_limit
    def add_bucket(self,bucket_name,access,zonename,create_date):
        try:
            bucket_count=len(self.conn.get_all_buckets())
            # print 'bucket_count is %s ' %bucket_count
            if bucket_count < self.bucket_limit:
                self.conn.create_bucket(bucket_name)
                b=self.conn.get_bucket(bucket_name)
                try:
                    # k=b.new_key('create_info')
                    # k.set_contents_from_string("{'bucket_name':'%s','zonename':'%s','access':'%s','create_date':'%s'}" %(bucket_name,zonename,access,create_date))
                    k1=Key(b)
                    k1.key='create_info'

                    #k1.set_metadata('Bucket_Name',bucket_name),注意，在设置元数据的时候key名不能带有下划线，该示例在创建的时候会报错403
                    k1.set_metadata('BucketName',bucket_name)
                    k1.set_metadata('ZoneName',zonename)
                    k1.set_metadata('Access',access)
                    k1.set_metadata('CreateDate',create_date)

                    k1.set_contents_from_string('')
                except Exception as e:
                    print r'\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\',e
                return True
            else:
                return False
        except Exception as e:
            return False

    def get_single_bucket(self,bucket_name):
        try:
            b=self.conn.get_bucket(bucket_name)
        except Exception as e:
            print e
        return b
    def get_object(self,bucket_name,object_name):
        try:
            b=self.conn.get_bucket(bucket_name)
            k=b.get_key(object_name)
        except Exception as e:
            print e
        return k

    def check_bucket(self,bucket_name):
        #验证己端是否存在相同bucket
        try:
            b=self.conn.get_bucket(bucket_name)
            if b:
                res = 'conflict'
                return res
        except boto.exception.S3ResponseError as e:
            return 'ok'
        # 验证全局是否存在相同bucket
        try:
            self.conn.create_bucket(bucket_name)
            self.conn.delete_bucket(bucket_name)
        except boto.exception.S3CreateError as e:
            print '_+_+_'*20,e
            res='conflict'
            return res
    def list_all_bucket(self):
        try:
            bucket_all_object=self.conn.get_all_buckets()
        except Exception as e:
            pass
        return bucket_all_object

    #查询
    def list_all(self):
        all_buckets=self.conn.get_all_buckets()
        for bucket in all_buckets:
            print u'容器名: %s' %(bucket.name)
            for key in bucket.list():
                print ' '*5,"%-20s%-20s%-20s%-40s%-20s" %(key.mode,key.owner.id,key.size,key.last_modified.split('.')[0],key.name)

    def list_single(self,bucket_name):
        try:
            single_bucket = self.conn.get_bucket(bucket_name)
        except Exception as e:
            print 'bucket %s is not exist' %bucket_name
            return
        print u'容器名: %s' % (single_bucket.name)
        for key in single_bucket.list():
            print ' ' * 5, "%-20s%-20s%-20s%-40s%-20s" % (key.mode, key.owner.id, key.size, key.last_modified.split('.')[0], key.name)

    #普通小文件下载：文件大小<=4M
    def dowload_file(self,filepath,key_name,bucket_name):
        all_bucket_name_list = [i.name for i in self.conn.get_all_buckets()]
        if bucket_name not in all_bucket_name_list:
            print 'Bucket %s is not exist,please try again' % (bucket_name)
            return
        else:
            bucket = self.conn.get_bucket(bucket_name)

        all_key_name_list = [i.name for i in bucket.get_all_keys()]
        if key_name not in all_key_name_list:
            print 'File %s is not exist,please try again' % (key_name)
            return
        else:
            key = bucket.get_key(key_name)

        if not os.path.exists(os.path.dirname(filepath)):
            print 'Filepath %s is not exists, sure to create and try again' % (filepath)
            return

        if os.path.exists(filepath):
            while True:
                d_tag = raw_input('File %s already exists, sure you want to cover (Y/N)?' % (key_name)).strip()
                if d_tag not in ['Y', 'N'] or len(d_tag) == 0:
                    continue
                elif d_tag == 'Y':
                    os.remove(filepath)
                    break
                elif d_tag == 'N':
                    return
        os.mknod(filepath)
        try:
            key.get_contents_to_filename(filepath)
        except Exception:
            pass

    # 普通小文件上传：文件大小<=4M
    def upload_file(self,filepath,key_name,bucket_name):
        try:
            bucket = self.conn.get_bucket(bucket_name)
        except Exception as e:
            print 'bucket %s is not exist' % bucket_name
            tag = raw_input('Do you want to create the bucket %s: (Y/N)?' % bucket_name).strip()
            while tag not in ['Y', 'N']:
                tag = raw_input('Please input (Y/N)').strip()
            if tag == 'N':
                return
            elif tag == 'Y':
                self.conn.create_bucket(bucket_name)
                bucket = self.conn.get_bucket(bucket_name)
        all_key_name_list = [i.name for i in bucket.get_all_keys()]
        if key_name in all_key_name_list:
            while True:
                f_tag = raw_input(u'File already exists, sure you want to cover (Y/N)?: ').strip()
                if f_tag not in ['Y', 'N'] or len(f_tag) == 0:
                    continue
                elif f_tag == 'Y':
                    break
                elif f_tag == 'N':
                    return
        key=bucket.new_key(key_name)
        if not os.path.exists(filepath):
            print 'File %s does not exist, please make sure you want to upload file path and try again' %(key_name)
            return
        try:
            f=file(filepath,'rb')
            data=f.read()
            key.set_contents_from_string(data)
        except Exception:
            pass

    def delete_file(self,key_name,bucket_name):
        all_bucket_name_list = [i.name for i in self.conn.get_all_buckets()]
        if bucket_name not in all_bucket_name_list:
            print 'Bucket %s is not exist,please try again' % (bucket_name)
            return
        else:
            bucket = self.conn.get_bucket(bucket_name)

        all_key_name_list = [i.name for i in bucket.get_all_keys()]
        if key_name not in all_key_name_list:
            print 'File %s is not exist,please try again' % (key_name)
            return
        else:
            key = bucket.get_key(key_name)

        try:
            bucket.delete_key(key.name)
        except Exception:
            pass

    def delete_bucket(self,bucket_name):
        all_bucket_name_list = [i.name for i in self.conn.get_all_buckets()]
        if bucket_name not in all_bucket_name_list:
            print 'Bucket %s is not exist,please try again' % (bucket_name)
            return
        else:
            bucket = self.conn.get_bucket(bucket_name)

        try:
            for key in bucket.get_all_keys():
                key.delete()
            self.conn.delete_bucket(bucket.name)
        except Exception:
            pass

    def delete_all_bucket(self):
        all_bucket = self.conn.get_all_buckets()
        for bucket in all_bucket:
            self.delete_bucket(bucket.name)

    #队列生成
    def init_queue(self,filesize,chunksize):   #8<<20 :8*2**20
        chunkcnt=int(math.ceil(filesize*1.0/chunksize))
        q=Queue.Queue(maxsize=chunkcnt)
        for i in range(0,chunkcnt):
            offset=chunksize*i
            length=min(chunksize,filesize-offset)
            c=Chunk(i+1,offset,length)
            q.put(c)
        return q

    #分片上传object
    def upload_trunk(self,filepath,mp,q,id):
        while not q.empty():
            chunk=q.get()
            fp=FileChunkIO(filepath,'r',offset=chunk.offset,bytes=chunk.length)
            mp.upload_part_from_file(fp,part_num=chunk.num)
            fp.close()
            q.task_done()

    #文件大小获取---->S3分片上传对象生成----->初始队列生成(--------------->文件切，生成切分对象)
    def upload_file_multipart(self,filepath,key_name,bucket_name,threadcnt=8):
        filesize=os.stat(filepath).st_size
        try:
            bucket=self.conn.get_bucket(bucket_name)
        except Exception as e:
            print 'bucket %s is not exist' % bucket_name
            tag=raw_input('Do you want to create the bucket %s: (Y/N)?' %bucket_name).strip()
            while tag not in ['Y','N']:
                tag=raw_input('Please input (Y/N)').strip()
            if tag == 'N':
                return
            elif tag == 'Y':
                self.conn.create_bucket(bucket_name)
                bucket = self.conn.get_bucket(bucket_name)
        all_key_name_list=[i.name for i in bucket.get_all_keys()]
        if key_name  in all_key_name_list:
            while True:
                f_tag=raw_input(u'File already exists, sure you want to cover (Y/N)?: ').strip()
                if f_tag not in ['Y','N'] or len(f_tag) == 0:
                    continue
                elif f_tag == 'Y':
                    break
                elif f_tag == 'N':
                    return

        mp=bucket.initiate_multipart_upload(key_name)
        q=self.init_queue(filesize,self.chrunksize)
        for i in range(0,threadcnt):
            t=threading.Thread(target=self.upload_trunk,args=(filepath,mp,q,i))
            t.setDaemon(True)
            t.start()
        q.join()
        mp.complete_upload()

    #文件分片下载
    def download_chrunk(self,filepath,key_name,bucket_name,q,id):
        while not q.empty():
            chrunk=q.get()
            offset=chrunk.offset
            length=chrunk.length
            bucket=self.conn.get_bucket(bucket_name)
            resp=bucket.connection.make_request('GET',bucket_name,key_name,headers={'Range':"bytes=%d-%d" %(offset,offset+length)})
            data=resp.read(length)
            fp=FileChunkIO(filepath,'r+',offset=chrunk.offset,bytes=chrunk.length)
            fp.write(data)
            fp.close()
            q.task_done()

    def download_file_multipart(self,filepath,key_name,bucket_name,threadcnt=8):
        all_bucket_name_list=[i.name for i in self.conn.get_all_buckets()]
        if bucket_name not in all_bucket_name_list:
            print 'Bucket %s is not exist,please try again' %(bucket_name)
            return
        else:
            bucket=self.conn.get_bucket(bucket_name)

        all_key_name_list = [i.name for i in bucket.get_all_keys()]
        if key_name not in all_key_name_list:
            print 'File %s is not exist,please try again' %(key_name)
            return
        else:
            key=bucket.get_key(key_name)

        if not os.path.exists(os.path.dirname(filepath)):
            print 'Filepath %s is not exists, sure to create and try again' % (filepath)
            return

        if os.path.exists(filepath):
            while True:
                d_tag = raw_input('File %s already exists, sure you want to cover (Y/N)?' % (key_name)).strip()
                if d_tag not in ['Y', 'N'] or len(d_tag) == 0:
                    continue
                elif d_tag == 'Y':
                    os.remove(filepath)
                    break
                elif d_tag == 'N':
                    return
        os.mknod(filepath)
        filesize=key.size
        q=self.init_queue(filesize,self.chrunksize)
        for i in range(0,threadcnt):
            t=threading.Thread(target=self.download_chrunk,args=(filepath,key_name,bucket_name,q,i))
            t.setDaemon(True)
            t.start()
        q.join()

    def generate_object_download_urls(self,key_name,bucket_name,valid_time=0):
        all_bucket_name_list = [i.name for i in self.conn.get_all_buckets()]
        if bucket_name not in all_bucket_name_list:
            print 'Bucket %s is not exist,please try again' % (bucket_name)
            return
        else:
            bucket = self.conn.get_bucket(bucket_name)

        all_key_name_list = [i.name for i in bucket.get_all_keys()]
        if key_name not in all_key_name_list:
            print 'File %s is not exist,please try again' % (key_name)
            return
        else:
            key = bucket.get_key(key_name)

        try:
            key.set_canned_acl('public-read')
            download_url = key.generate_url(valid_time, query_auth=False, force_http=True)
            if self.port != 80:
                x1=download_url.split('/')[0:3]
                x2=download_url.split('/')[3:]
                s1=u'/'.join(x1)
                s2=u'/'.join(x2)

                s3=':%s/' %(str(self.port))
                download_url=s1+s3+s2
                print download_url

        except Exception:
            pass



if __name__ == '__main__':
    #约定：
    #1:filepath指本地文件的路径(上传路径or下载路径),指的是绝对路径
    #2:bucket_name相当于文件在对象存储中的目录名或者索引名
    #3:key_name相当于文件在对象存储中对应的文件名或文件索引

    access_key = "65IY4EC1BSFYNH6SHWGW"
    secret_key = "viNfIftLHhrPt2MYK44DkWGvxZb82aYqLrCzGYLx"

    access_key="QHHYSEW3F3BEEYCL5LOD"

    secret_key="fkbQnGsF2c2Ufv5kvQOaiA0qvo926xDZMgO0vtty"
    ip='172.16.201.36'
    port=8080
    conn=CONNECTION(access_key,secret_key,ip,port)
    #查看所有bucket以及其包含的文件
    #conn.list_all()

    #简单上传,用于文件大小<=8M
    # conn.upload_file('/etc/passwd','passwd','test_bucket01')
    #查看单一bucket下所包含的文件信息
    # conn.list_single('test_bucket01')


    #简单下载,用于文件大小<=8M
    # conn.dowload_file('/lhf_test/test01','passwd','test_bucket01')
    # conn.list_single('test_bucket01')

    #删除文件
    # conn.delete_file('passwd','test_bucket01')
    # conn.list_single('test_bucket01')
    #
    #删除bucket
    # conn.delete_bucket('test_bucket01')
    # conn.list_all()

    #切片上传(多线程),用于文件大小>8M,8M可修改，但不能小于8M
    # conn.upload_file_multipart('/etc/passwd','passwd_multi_upload','test_bucket01')
    # conn.list_single('test_bucket01')

    # 切片下载(多线程),用于文件大小>8M,8M可修改，但不能小于8M
    # conn.download_file_multipart('/lhf_test/passwd_multi_dowload','passwd_multi_upload','test_bucket01')

    #生成下载url
    #conn.generate_object_download_urls('passwd_multi_upload','test_bucket01')
    #conn.list_all()





    #conn.list_single('my-new-bucket10')
    # conn.upload_file('/etc/passwd','test','my-new-bucket10')
    # conn.list_single('my-new-bucket10')

    #conn.upload_file_multipart('/dev/a.txt','a.txt_multi','my-new-bucket112')
    #conn.list_single('my-new-bucket112')
    #conn.dowload_file('/test/passwd','passwd','my-new-bucket10')

    #conn.download_file_multipart('/dev/a.txt','a.txt_multi','my-new-bucket112')

    #conn.generate_object_download_urls('a.txt_multi','my-new-bucket112')
    conn.list_all()
    zonename='beijing'
    access='private'
    create_time='123123123123213123123'

    # conn.delete_bucket('lhf_test1')
    # conn.delete_bucket('lhf_test2')
    conn.delete_bucket('lhf_test8')
    # conn.delete_bucket('lhf_test10')
    # conn.add_bucket('lhf_test1',access,zonename,create_time)
    # conn.add_bucket('lhf_test8',access,zonename,create_time)

    conn.delete_all_bucket()