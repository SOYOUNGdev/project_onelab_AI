import math
import mimetypes
import os
from decimal import Decimal
from urllib.parse import urlparse
import pandas as pd
from docx import Document
import pymupdf
import fitz

import time
import pandas as pd
import cv2
import json
import matplotlib.pyplot as plt

import shutil
import os
import random

import requests
import uuid
import time
import json

from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, F, Q, Subquery, Count, Sum
from django.db.models.fields.files import ImageFieldFile
from django.http import JsonResponse, FileResponse
from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
import json
from rest_framework.views import APIView

from community.models import Community
from file.models import File
from like.models import Like
from member.models import Member, MemberFile
from onelab.models import OneLab
from onelabMember.models import OneLabMember
from point.models import Point
from review.models import Review
from share.models import Share, ShareFile, ShareReview, ShareLike, SharePoints, ShareFileContent
from oneLabProject.settings import MEDIA_URL
from shareMember.models import ShareMember
from university.models import University

from django.views import View
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Avg
from .models import Share, ShareReview, ShareLike, ShareFile
from university.models import University
from onelab.models import OneLab
from member.models import MemberFile, Member
from like.models import Like
from decimal import Decimal
from django.conf import settings

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

from django.conf import settings
import os


def get_file_content(file_path, file_id):
    # ImageFieldFile 객체를 문자열로 변환
    file_path_str = str(file_path)

    # 파일 경로에서 "../upload/" 제거
    if file_path_str.startswith("../upload/"):
        file_path_str = file_path_str.replace("../upload/", "")

    # 절대 경로 생성
    file_path_full = os.path.join(settings.MEDIA_ROOT, file_path_str)

    if file_path_str.lower().endswith('.hwp'):
        with open(file_path_full, 'r', encoding='utf-8') as file:
            file_content = file.read()
        return file_content
    elif file_path_str.lower().endswith('.docx'):
        file_content = get_docx_content(file_path)
        return file_content
    elif file_path_str.lower().endswith('.pdf'):
        file_content = get_pdf_to_img(file_path, file_id)
        return file_content
    elif file_path_str.lower().endswith('.xlsx'):
        file_content = get_excel_content(file_path)
        return file_content
    else:
        return '다름'

def get_excel_content(file_path):
    try:
        # 엑셀 파일을 읽어서 DataFrame으로 변환
        df = pd.read_excel(file_path)
        # DataFrame을 문자열로 변환하여 반환
        file_content = df.to_string()
        return file_content
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error in reading file: {file_path}")
        print(e)
        return None

def get_docx_content(file_path):
    try:
        doc = Document(file_path)
        # 문단별로 텍스트를 추출하여 리스트로 저장
        paragraphs = [paragraph.text for paragraph in doc.paragraphs]
        # 리스트를 하나의 문자열로 결합하여 반환
        file_content = '\n'.join(paragraphs)
        return file_content
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error in reading file: {file_path}")
        print(e)
        return None

def get_pdf_to_img(file_path, file_id):
    local_file_path = os.path.join(settings.MEDIA_ROOT, str(file_path))
    output_dir = os.path.join(settings.MEDIA_ROOT, "share/image/")

    os.makedirs(output_dir, exist_ok=True)

    try:
        doc = fitz.open(local_file_path)
        first_page = doc.load_page(0)
        pixmap = first_page.get_pixmap()
        output_image_path = os.path.join(output_dir, f"{file_id}.png")
        pixmap.save(output_image_path)

        full_text = get_img_to_content(output_image_path)

        return full_text

    except Exception as e:
        print(f"오류 발생: {e}")

def get_img_to_content(output_image_path):
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 5000)

    secret_key = 'c2Z3Qk5NZFl1c1poTVFWRkh3cG1zbGZoTWVhTXNEQkU='
    api_url = 'https://v0ozwri6qr.apigw.ntruss.com/custom/v1/31037/247390edd22db10357954c4ca8730e1c49122c5365221fb7aada0ac3083455b3/general'
    image_file = output_image_path

    request_json = {
        'images': [
            {
                'format': 'png',
                'name': 'demo'
            }
        ],
        'requestId': str(uuid.uuid4()),
        'version': 'V2',
        'timestamp': int(round(time.time() * 1000))
    }

    payload = {'message': json.dumps(request_json).encode('UTF-8')}
    files = [('file', open(image_file, 'rb'))]
    headers = {'X-OCR-SECRET': secret_key}

    response = requests.request("POST", api_url, headers=headers, data=payload, files=files)

    image = cv2.imread(image_file)
    highlighted_image = image.copy()

    if response.status_code == 200:
        ocr_results = json.loads(response.text)
        all_texts = []
        for image_result in ocr_results['images']:
            for field in image_result['fields']:
                text = field['inferText']
                all_texts.append(text)

                bounding_box = field['boundingPoly']['vertices']
                start_point = (int(bounding_box[0]['x']), int(bounding_box[0]['y']))
                end_point = (int(bounding_box[2]['x']), int(bounding_box[2]['y']))
                cv2.rectangle(highlighted_image, start_point, end_point, (0, 0, 255), 2)

        full_text = ' '.join(all_texts)
        return full_text
    else:
        print(f"OCR 결과를 받아오지 못했습니다. 상태 코드: {response.status_code}")


def calculate_word_similarity(file_contents):
    count_v = CountVectorizer(tokenizer=lambda x: x.split())
    count_matrix = count_v.fit_transform(file_contents)
    cosine_sim = cosine_similarity(count_matrix)
    return cosine_sim


def find_similar_posts(all_posts, current_file):
    # 모든 ShareFileContent의 text를 리스트로 가져옴
    file_contents = [current_file.text]  # 현재 파일의 텍스트를 추가합니다.
    for post in all_posts:
        content = post.text
        if content:
            file_contents.append(content)

    # 단어 기준 코사인 유사도 계산
    cosine_sim = calculate_word_similarity(file_contents)

    # 현재 게시물의 파일 내용과의 유사도가 높은 내용 선택
    similarities_to_doc = cosine_sim[0]  # 첫 번째 행은 현재 파일과 다른 파일들의 유사도
    sorted_indices = similarities_to_doc.argsort()[::-1]

    # 자기 자신을 제외한 인덱스 리스트 생성 (0번 인덱스를 제외)
    sorted_indices = [int(idx) for idx in sorted_indices if idx != 0]

    if not sorted_indices:  # sorted_indices가 비어 있는 경우
        return []

    # 상위 4개의 유사한 게시물 선택 (리스트 길이가 4보다 작을 경우 모든 게시물 선택)
    selected_indices = sorted_indices[1:5] if len(sorted_indices) >= 4 else sorted_indices
    print(selected_indices)
    # 유사한 게시물 리스트 생성
    similar_posts = [(all_posts[idx - 1], similarities_to_doc[idx]) for idx in selected_indices]

    return similar_posts


class ShareDetailView(View):
    def get(self, request, id):
        post = Share.objects.get(id=id)

        university_member = University.objects.get(member=post.university)
        post_list = Share.enabled_objects.filter(university=university_member).order_by('-id')
        page = request.GET.get('page', 1)
        paginator = Paginator(post_list, 4)
        posts = paginator.page(page)

        # 파일 가져오기
        for p in posts:
            first_file = p.sharefile_set.first()
            if first_file:
                file_name = first_file.path.name
                file_extension = file_name.split('.')[-1].lower()  # 파일 확장자 추출
                p.file_extension = file_extension
                # 파일이 있으면 파일의 경로를 기반으로 URL 생성
                p.image_url = f"{MEDIA_URL}{first_file.path}"
                p.file_content = get_file_content(first_file.path, first_file.file_id)
            else:
                p.image_url = None
                p.file_content = None

        # 리뷰 평균과 개수
        reviews = ShareReview.enabled_objects.filter(share_id=post.id)
        if len(reviews) > 0:
            review_count = reviews.count()
            review_avg_decimal = reviews.aggregate(avg_rating=Avg('review__review_rating'))['avg_rating']
            review_avg_rounded = Decimal(review_avg_decimal).quantize(Decimal('0.1'))
        else:
            review_count = 0
            review_avg_rounded = 0.0

        # 좋아요 수
        share_like_count = ShareLike.objects.filter(share=post).count()

        # 원랩 수
        onelabs = OneLab.objects.filter(university=university_member)
        onelab_count = onelabs.count()

        # 회원이 좋아요를 한 상태인지
        member = Member.objects.get(id=request.session['member']['id'])
        share_likes = ShareLike.objects.filter(share=post)
        member_like = False
        for share_like in share_likes:
            try:
                # 해당 Like 객체를 가져옵니다.
                like_object = Like.objects.get(member=member, like_status=True, id=share_like.like_id)
                # 예외가 발생하지 않았으므로, 해당 Like 객체가 존재합니다.
                member_like = True
            except Like.DoesNotExist:
                # 해당 Like 객체가 존재하지 않습니다.
                member_like = False

        profile = MemberFile.objects.filter(member=university_member.member)
        if profile:
            profile = profile[0]
        # print(profile.path)

        # 전체 파일의 텍스트 가져오기
        all_posts = ShareFileContent.objects.all().order_by('-share_id')

        # 현재 게시물의 file 객체 찾기
        # current_file = post.sharefile_set.first()
        # 현재 게시물의 텍스트가 들어있는 테이블에서 현재 파일 객체 찾기
        current_file = post.sharefilecontent_set.get(share=post)

        # 유사한 게시물 찾기
        similar_posts = find_similar_posts(all_posts, current_file)
        similar_lists = []

        for similar_post, similarity in similar_posts:
            share = Share.objects.get(id=similar_post.share_id)
            similar_lists.append(share)

        context = {
            'share': post,
            'share_files': list(post.sharefile_set.all()),
            'posts': posts,
            'review_count': review_count,
            'review_avg_rounded': review_avg_rounded,
            'share_like_count': share_like_count,
            'onelab_count': onelab_count,
            'university_member': university_member,
            'member_like': member_like,
            'profile': profile.path,
            'similar_posts': similar_lists,  # 유사한 게시물 추가
        }

        for similar_post, similarity in similar_posts:
            share = Share.objects.get(id=similar_post.share_id)
            print(share.id, similarity)

        return render(request, 'share/detail.html', context)

    # ------------------------------------------------------------------------------
    def post(self, request, id):
        post = Share.objects.get(id=id)  # 자료공유 상세보기 아이디를 가져옴
        member = request.session['member']['id']
        university = post.university_id
        price = post.share_points
        share_member = University.objects.get(member=university)  # 판매자
        pay_member = University.objects.get(member=member)  # 구매자
        # 결제 버튼 클릭 시 기능
        share_member_id = share_member.member_id  # 판매자 실제 아이디
        Point.objects.create(member_id=share_member_id, point_status=3, point=price)
        pay_member_id = pay_member.member_id  # 구매자 실제 아이디
        point = Point.objects.create(member_id=pay_member_id, point_status=2, point=price)

        share_data = {
            'points_id': point.id,
            'share_id': post.id
        }
        SharePoints.objects.get_or_create(**share_data)

        if pay_member.university_member_points < price:
            return render(request, 'share/list.html')
        else:
            # ------ 적립, 사용 잔액 기능 구현 --------------- #
            share_member.university_member_points += price
            before = share_member.save()
            print(before)
            # ----- 판매자는 적립금액 들어옴 --------------#
            pay_member.university_member_points -= price
            after = pay_member.save()
            print(after)
            # ----- 구매자는 사용금액 차감됨 -------------- #

        # ----멤버 결제 내역 기능 시작 --------------#
        join_data = {
            'share_member_status': 0,
            'university_id': request.session['member']['id'],
            'share_id': post.id
        }
        ShareMember.objects.get_or_create(**join_data)
        # ------- 멤버 결제 내역 기능 완료 --------- #
        return redirect('/myPage/main/')


# 좋아요를 누를 때마다 들어오는 View

class ShareLikeView(View):
    @transaction.atomic
    def post(self, request):
        # 요청 방식이 post이고, ajax라면
        if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # # JSON 데이터 파싱
            data = json.loads(request.body)
            # body에 있는 share_id 가져와서 share_id 선언
            share_id = data.get('share_id')
            # 해당 share_id 가진 게시글 가져오기
            share = Share.objects.get(id=share_id)
            # 세션에 들어있는 회원
            member = Member.objects.get(id=request.session['member']['id'])

            try:
                # 해당 회원이 이 게시글에 대해 좋아요를 한 경우
                share_like = ShareLike.objects.get(share=share, like__member=member)
                if share_like.like.like_status:
                    # 이미 좋아요한 경우, 좋아요 취소
                    share_like.like.like_status = False
                    share_like.like.save()  # like_status를 False로 변경
                    share_like.delete()  # 좋아요 삭제
                else:
                    # 이미 좋아요를 취소한 경우
                    # like_status를 True로 변경하여 다시 좋아요를 한 것으로 처리
                    share_like.like.like_status = True
                    share_like.like.save()  # like_status를 True로 변경
            except ShareLike.DoesNotExist:
                # 해당 회원이 이 게시글에 대해 좋아요를 하지 않은 경우
                # 좋아요 생성
                like = Like.objects.create(member=member, like_status=True)
                share_like = ShareLike.objects.create(share=share, like=like)

            # 업데이트 된 좋아요 수 응답하기
            share_like_count = ShareLike.objects.filter(share=share).count()
            return JsonResponse({'like_count': share_like_count})

        # AJAX 요청이 아닌 경우, 상세보기 페이지로 이동
        return render(request, 'share/detail.html')

# 자료 공유 글 작성할 때 view
class ShareWriteView(View):
    # 작성 페이지로 이동할 때
    @transaction.atomic
    def get(self, request):
        # 로그인 되어있는 회원 객체 -> member로 선언
        member = Member.objects.get(id=request.session['member']['id'])
        # 대학생 회원만 자료공유 글을 작성할 수 있음
        # member객체가 member인 학교 회원 객체 1개 가져와 university_member로 선언
        university_member = University.objects.get(member=member)

        # 학교 이메일 도메인 부분 추출
        school_domain = member.member_school_email.split('@')[1]

        if 'kaist' in member.member_school_email:
            university_member.university_member_school = '카이스트'
        elif 'snu' in member.member_school_email:
            university_member.university_member_school = '서울대학교'
        elif 'yonsei' in member.member_school_email:
            university_member.university_member_school = '연세대학교'
        elif 'korea' in member.member_school_email:
            university_member.university_member_school = '고려대학교'
        else:
            university_member.university_member_school = school_domain

        university_member.save()

        # 마이 포인트 계산
        # member=member이고 point_status=3인 point객체가 있다면
        if len(list(Point.objects.filter(member=member, point_status=3))) > 0:
            # Sum과 aggregate함수를 이용하여 해당 포인트들의 합을 구한 뒤, point로 선언
            point = Point.objects.filter(member=member, point_status=3).aggregate(Sum('point'))['point__sum']
        else:
            # 로그인 한 회원의 포인트 내역이 없다면, insert
            point = Point.objects.create(member=member, point_status=3).point

        # 마이 포스트 수
        # 로그인 한 회원이 작성한 글 수 구하기
        # 자료글
        share_post_count = Share.enabled_objects.filter(university=university_member).count()
        # 커뮤니티 글
        community_post_count = Community.enabled_objects.filter(
            member=member).count()  # community, onelab도 enabled_objects로 바꾸기
        # 원랩 글
        onelab_post_count = OneLab.enabled_objects.filter(university=university_member).count()
        # 집계함수를 통해 구한 글들 모두 합한 총 개수 -> total_post_count로 선언
        total_post_count = share_post_count + community_post_count + onelab_post_count

        # 마이 원랩 수
        # 회원이 들어가 있는 원랩 전부 가져오기
        onelabs = OneLab.objects.filter(university=university_member)
        # 집계함수를 이용 -> 총 개수 onelab_count로 선언
        onelab_count = onelabs.count()

        # 위에서 가져온 데이터들 data에 dict 타입으로 저장
        data = {
            'point': point,
            'total_post_count': total_post_count,
            'onelab_count': onelab_count,
        }
        # 글 작성 페이지 이동, data함께 전달
        return render(request, 'share/write.html', data)

    @transaction.atomic
    def post(self, request):
        # 회면에서 post로 받아온 데이터를 data에 저장
        data = request.POST
        # input 태그 하나에 여러 파일일 때(multiple), getlist('{input태그 name값}')
        # 파일이 여러개 이므로 getlist로 가져와서 files에 따로 저장
        file = request.FILES

        # input 태그 하나 당 파일 1개 일 떄
        # file = request.FILES

        # 로그인 되어있는 회원 -> member
        member = University.objects.get(member_id=request.session['member']['id'])

        # 위에서 받아온 data의 name을 사용하여 맞는 데이터들을 dict타입의 data로 선언
        data = {
            'share_title': data['share-title'],
            'share_points': data['share-points'],
            'share_choice_major': data['share-choice-major'],
            'share_choice_grade': data['share-choice-grade'],
            'share_content': data['share-content'],
            'share_type': data['share-type'],
            'share_text_major': data['share-text-major'],
            'share_text_name': data['share-text-name'],
            'university': member,
        }

        # 작성 된 글 insert
        share = Share.objects.create(**data)

        # 가져온 파일들 하나씩 반복
        for key, file in file.items():
            # 업로드된 파일을 File 모델에 저장
            file_instance = File.objects.create(file_size=file.size)
            # 만든 파일 객체를 PlaceLike 모델에 저장
            create_file = ShareFile.objects.create(share=share, file=file_instance, path=file)
            # 파일에 있는 내용만 읽어와서 share_file_content 테이블에 저장
            file_text = get_file_content(create_file.path, create_file.file_id)
            ShareFileContent.objects.create(share=share, file_name=file.name, text=file_text)


        # 작성한 게시글의 상세보기 페이지로 이동
        return redirect(reverse('share:detail', kwargs={'id': share.id}))

# 파일 다운로드 시에 들어오는 view
class ShareDownloadView(View):
    def get(self, request, file_path, *args, **kwargs):
        # 파일 경로에서 파일 이름 추출
        file_name = file_path.split('/')[-1]

        # 파일 시스템 스토리지 인스턴스 생성
        fs = FileSystemStorage()

        # 파일의 MIME 타입 추측
        content_type, _ = mimetypes.guess_type(file_name)
        # 파일 응답 생성
        response = FileResponse(fs.open(file_path, 'rb'),
                                content_type=content_type)
        # 다운로드 시 파일 이름으로 설정
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        # 응답
        return response

# 수정하기 시에 들어오는 view
class ShareUpdateView(View):
    # 글 수정하기 페이지 들어올 때, 해당 게시글의 id함께 받아옴
    @transaction.atomic
    def get(self, request, id):
        # 로그인 된 회원 -> member -> university_member
        member = Member.objects.get(id=request.session['member']['id'])
        university_member = University.objects.get(member=member)

        # 마이 포인트 계산
        # member=member이고 point_status=3인 point객체가 있다면
        if len(list(Point.objects.filter(member=member, point_status=3))) > 0:
            # Sum과 aggregate함수를 이용하여 해당 포인트들의 합을 구한 뒤, point로 선언
            point = Point.objects.filter(member=member, point_status=3).aggregate(Sum('point'))['point__sum']
        else:
            # 로그인 한 회원의 포인트 내역이 없다면, insert
            point = Point.objects.create(member=member, point_status=3)

        # 마이 포스트 수
        # 로그인 한 회원이 작성한 글 수 구하기
        # 자료글
        share_post_count = Share.enabled_objects.filter(university=university_member).count()
        # 커뮤니티 글
        community_post_count = Community.enabled_objects.filter(
            member=member).count()
        # 원랩 글
        onelab_post_count = OneLab.enabled_objects.filter(university=university_member).count()
        # 집계함수를 통해 구한 글들 모두 합한 총 개수 -> total_post_count로 선언
        total_post_count = share_post_count + community_post_count + onelab_post_count

        # 마이 원랩 수
        # 회원이 들어가 있는 원랩 전부 가져오기
        onelabs = OneLab.objects.filter(university=university_member)
        # 집계함수를 이용 -> 총 개수 onelab_count로 선언
        onelab_count = onelabs.count()

        # 전달받은 id이용 -> 수정하는 place객체 가져와서 post로 선언
        post = Share.objects.get(id=id)
        # update_url 생성
        update_url = reverse('share:update', args=[id])
        # 위에서 가져온 데이터들 dict 타입으로 context에 저장
        context = {
            'share': post,
            'share_files': list(post.sharefile_set.all()),
            'update_url': update_url,
            'point': point,
            'total_post_count': total_post_count,
            'onelab_count': onelab_count,
        }
        # 수정하기 페이지로 이동, context함께 전달
        return render(request, 'share/update.html', context)

    # 수정 완료 시
    def post(self, request, id):
        # post방식으로 받아온 데이터들 data로 선언
        data = request.POST
        # 기존의 Share 객체 가져오기
        share = Share.objects.get(id=id)

        # 가져온 name값으로 가져온 데이터들 모두 update하기
        share.share_title = data['share-title']
        share.share_content = data['share-content']
        share.share_choice_major = data['share-choice-major']
        share.share_choice_grade = data['share-choice-grade']
        share.share_type = data['share-type']
        share.share_points = data['share-points']
        share.share_text_name = data['share-text-name']
        share.share_text_major = data['share-text-major']
        share.save(
            update_fields=['share_title', 'share_content', 'share_choice_major', 'share_choice_grade', 'share_type',
                           'share_points', 'share_text_name', 'share_text_major'])

        # 새로운 파일들이 있는지 확인
        files = request.FILES.getlist('upload-file')

        # 새로운 파일들이 없는 경우 기존 파일들 유지
        if not files:
            # 수정된 Share의 상세 페이지로 이동
            return redirect(share.get_absolute_url())

        # 기존의 파일들 삭제
        share.sharefile_set.all().delete()

        # 새로운 파일들 처리
        for file in files:
            # 파일 저장
            file_instance = File.objects.create(file_size=file.size)
            ShareFile.objects.create(share=share, file=file_instance, path=file)

        # 수정된 share글 의 상세 페이지로 이동
        return redirect(share.get_absolute_url())

# 삭제하기 view
class ShareDeleteView(View):
    def get(self, request):
        # 해당 게시글 soft_delete 방식으로 post_status를 False로 update
        share_id = request.GET['id']
        Share.objects.filter(id=share_id).update(share_post_status=False)  # 수정
        # 삭제 후에는 리스트 페이지로 이동
        return redirect('/share/list')

# 게시글 리스트 view
class ShareListView(View):
    def get(self, request):
        # 게시글 리스트 페이지 이동
        return render(request, 'share/list.html')

# rest방식의 리스트 view
class ShareListAPIView(APIView):
    @transaction.atomic
    def get(self, request, page):
        # 한 페이지에 보여줄 장소의 개수와 페이지
        row_count = 12

        # 시작 번호 -> offset
        offset = (page - 1) * row_count
        # 끝 번호 -> limit
        limit = page * row_count

        # 가져올 데이터들 먼저 리스트에 담기
        datas = [
            'id',
            'share_title',
            'share_points',
            'share_choice_major',
            'created_date',
            'member_name',
            'university_name',
            'share_like_count',
            'share_choice_grade',
        ]

        # 학년 필터
        # default는 전체 학년
        grade_sort = request.GET.get('gradeSort', 'all')
        # 전달된 정렬 방식이 전체일 경우
        if grade_sort == 'all':
            # 모든 자료글 가져오기
            shares = Share.enabled_objects.all()
        else:
            # 해당 학년에 속하는 글만 가져오기
            shares = Share.enabled_objects.filter(share_choice_grade__contains=grade_sort)

        # 학과 필터
        # default는 전체
        major_sort = request.GET.get('majorSort', 'all')
        # 전체가 아닐 경우, 해당된 학과에 속한 글만 가져오기
        if major_sort != 'all':
            shares = shares.filter(share_choice_major__contains=major_sort)

        # 인기순 필터
        # default는 최신순
        sort_order = request.GET.get('sortOrder', 'latest')
        # 최신순이 아닐경우
        if sort_order != 'latest':
            # 좋아요 수를 Count를 이용하여 계산한뒤 share_like_count로 별칭
            # 좋아요 수가 많은 순으로, 같다면 최신순으로 정렬
            shares = shares.annotate(share_like_count=Count('sharelike')).order_by('-share_like_count', '-id')
        else:
            # 최신순일 경우
            shares = shares.annotate(share_like_count=Count('sharelike')).order_by('-id')

        # 필터링 된 자료글들에 작성자 이름과, 학교명에 별칭
        # 리스트에 담아뒀던 data들 넣어주기
        shares = shares.annotate(member_name=F('university__member__member_name'),
                                 university_name=F('university__university_member_school')) \
            .values(*datas)
        # 필터링 된 게시글 개수
        share_count = shares.count()
        # 시작~끝에 해당되는 게시글만 가져오기
        shares = shares[offset:limit]

        # 다음 페이지가 있는지 계산
        has_next = share_count > offset + limit

        # response할 데이터 담기
        share_info = {
            'shares': [],
            'hasNext': has_next,
            'member_like': {},
        }

        # 자료 하나씩 반복
        for share in shares:
            # 자료의 id
            share_one_id = share['id']
            # 자료의 id이용하여 글 객체 1개 가져오기 -> share_one
            share_one = Share.objects.get(id=share_one_id)
            # 자료글과 연관된 파일들 가져오기 -> share_files
            share_files = share_one.sharefile_set.all()

            # 자료공유 파일 데이터를 리스트에 추가
            share_file_info = []
            for file in share_files:
                file_info = {
                    'id': file.pk,
                    'path': file.path.url,  # 파일의 경로
                    'file_extension': file.path.url.split('.')[-1].lower()  # 확장자
                }
                share_file_info.append(file_info)

            # 리뷰 정보에 파일 정보를 추가
            share['share_files'] = share_file_info

            # 회원이 좋아요를 한 상태인지
            # 로그인 된 회원 객체 -> member
            member = Member.objects.get(id=request.session['member']['id'])

            # 해당 자료에 대한 회원의 좋아요 여부 확인
            try:
                like_object = ShareLike.objects.get(like__member=member, like__like_status=True, share=share_one)
                share_info['member_like'][share_one_id] = True
            except ShareLike.DoesNotExist:
                share_info['member_like'][share_one_id] = False

            share_info['shares'].append(share)

        # 자료 데이터 응답
        return Response(share_info)

# 리뷰리스트 view
class ShareReviewListView(View):
    def get(self, request):
        # URL에서 전달된 ID 값 가져오기
        share_id = request.GET.get('share_id')
        # 가져온 ID를 이용하여 해당하는 게시글 -> post로 선언
        post = Share.objects.get(id=share_id)
        # 좋아요 수 -> share_like_count로 선언
        share_like_count = ShareLike.objects.filter(share=post).count()

        # 파일
        share = Share.objects.get(id=share_id)
        share_file = ShareFile.objects.filter(share=share).first()
        # 확장자
        share_file_extension = share_file.file_extension

        # 원랩 수
        share_member = University.objects.get(member=share.university)
        # 집계함수 이용 -> 작성자가 속해있는 원랩 수
        # 원랩장인 경우
        onelab_manager_count = OneLab.objects.filter(university=share_member).count()
        # 원랩 멤버인 경우
        onelab_member_count = OneLabMember.objects.filter(university=share_member).count()
        # 총 원랩 수
        total_onelab_count = onelab_manager_count + onelab_member_count

        # 상세 페이지 내에 들어갈 작성자의 글
        # 작성자가 현재 게시글(post)의 작성자와 같은 글들 중, 삭제되지 않은 글들만 최신순으로 가져오기
        post_list = Share.enabled_objects.filter(university=share_member).order_by('-id')
        # Paginator를 사용하여 최신글 4개만 가져와서 posts로 선언
        page = request.GET.get('page', 1)
        paginator = Paginator(post_list, 4)
        posts = paginator.page(page)

        # 회원이 좋아요를 한 상태인지
        member = Member.objects.get(id=request.session['member']['id'])
        share_likes = ShareLike.objects.filter(share=share)
        member_like = False
        for share_like in share_likes:
            try:
                # 해당 Like 객체를 가져옵니다.
                like_object = Like.objects.get(member=member, like_status=True, id=share_like.like_id)
                # 해당 Like 객체가 존재
                # 로그인된 회원이 해당 게시글에 좋아요를 한 상태이므로, member_like를 True로 변경
                member_like = True
            except Like.DoesNotExist:
                # 해당 Like 객체가 존재하지 않을경우
                member_like = False

        # 해당 회원의 프로필이미지 가져오기
        profile = MemberFile.objects.filter(member=share_member.member)
        if profile:
            profile = profile[0]

        # 페이지 이동 시, 함께 전달해야할 데이터들 postData에 dict타입으로 저장
        post_data = {
            'share_id': post.id,
            'share_title': post.share_title,
            'share_points': post.share_points,
            'share_content': post.share_content,
            'university_member_school': post.university.university_member_school,
            'university_member_major': post.university.university_member_major,
            'share_text_name': post.share_text_name,
            'member_name': post.university.member.member_name,
            'share_text_major': post.share_text_major,
            'share_choice_major': post.share_choice_major,
            'share_choice_grade': post.share_choice_grade,
            'file_path': post.sharefile_set.all().values('path'),
            'share_like_count': share_like_count,
            'share_file_extension': share_file_extension,
            'total_onelab_count': total_onelab_count,
            'member_like': member_like,
            'posts': posts,
            'profile': profile.path,
        }

        # 리뷰 페이지 이동, post_data 함께 전달
        return render(request, 'share/review.html', post_data)

# rest방식의 리뷰리스트 view
class ShareReviewListAPIView(APIView):
    # 게시글 id와 page 함께 받음
    @transaction.atomic
    def get(self, request, share_id, page):
        # 한페이지에 5개씩 보여주기 위해 row_count = 5로 선언
        row_count = 5

        # 시작 번호 -> offset
        offset = (page - 1) * row_count
        # 끝 번호 -> limit
        limit = page * row_count

        # 리뷰페이지에 필요한 데이터들 datas에 저장
        datas = [
            'review__id',
            'review__review_content',
            'review__review_rating',
            'member_name',
            'review__member',
            'review__member__member_school_email',
            'review__created_date',
        ]

        # 정렬 방식에 따라 쿼리셋을 정렬(초기에는 latest/최신순 정렬)
        sort = request.GET.get('sort', 'latest')
        # 전달받은 정렬 방식이 별점 높은 순일 경우
        if sort == 'highest_rating':
            # 해당되는 리뷰글을 가져온다(시작~끝에 해당되는 글만)
            # 리뷰를 작성한 member의 이름에는 annotate를 사용하여 별칭을 붙여준다
            # 리뷰글에 필요한 값은 위에서 먼저 담아놓은 datas
            # 정렬은 평점순 -> 같다면 최신순
            reviews = ShareReview.enabled_objects.filter(share_id=share_id).annotate(
                member_name=F('review__member__member_name')) \
                .values(*datas).order_by('-review__review_rating', '-review__created_date')
        # 전달받은 정렬 방식이 별점 낮은 순일 경우
        elif sort == 'lowest_rating':
            reviews = ShareReview.enabled_objects.filter(share_id=share_id).annotate(
                member_name=F('review__member__member_name')) \
                .values(*datas).order_by('review__review_rating', '-review__created_date')
        # 전달받은 정렬 방식이 최신순일 경우
        else:
            reviews = ShareReview.enabled_objects.filter(share_id=share_id).annotate(
                member_name=F('review__member__member_name')) \
                .values(*datas).order_by('-review__created_date')

        reviews = reviews[offset:limit]
        # 리뷰 개수 가져오기
        total_review_count = ShareReview.enabled_objects.filter(share_id=share_id).count()

        # 리뷰가 없을 때 처리
        if total_review_count == 0:
            return Response({
                'reviews': [], 'hasNext': False, 'share_id': share_id, 'review_count': 0.0, 'review_avg': 0.0
            })

        # 리뷰 평균
        review_avg_decimal = \
            ShareReview.enabled_objects.filter(share_id=share_id).aggregate(avg_rating=Avg('review__review_rating'))[
                'avg_rating']
        review_avg_rounded = Decimal(review_avg_decimal).quantize(Decimal('0.1'))  # 수정

        # 다음 페이지가 있는지 계산할 때도 전체 리뷰 개수를 사용하여 계산
        has_next = total_review_count > offset + limit

        # 리뷰 개수와 평균을 response에 추가
        review_info = {
            'reviews': [],
            'hasNext': has_next,
            'share_id': share_id,
            'review_count': total_review_count,  # 전체 리뷰 개수 사용
            'review_avg': float(review_avg_rounded),  # 반올림된 값
        }
        # 가져온 리뷰들 하나씩 반복
        for review in reviews:
            # 리뷰의 id
            review_one_id = review['review__id']
            # 해당 리뷰 id로 리뷰 객체 가져오기
            review_one = Review.objects.get(id=review_one_id)
            # 해당 리뷰 객체와 연관되어있는 파일들 가져오기
            review_files = review_one.reviewfile_set.all()
            # 리뷰를 작성한 member의 id
            member_one_id = review['review__member']
            # 해당 member의 프로필이미지 가져오기
            member_profiles = MemberFile.objects.filter(member_id=member_one_id)

            # 리뷰 파일 데이터를 리스트에 추가
            review_file_info = []
            for file in review_files:
                # file_info에는 id와 path가 저장됨
                file_info = {
                    'id': file.pk,
                    'path': file.path.url  # 파일의 경로
                }
                review_file_info.append(file_info)

            # 리뷰 정보에 파일 정보를 추가
            review['review_files'] = review_file_info

            # 멤버 프로필 이미지 리스트에 추가
            profile_file_info = []
            for profile in member_profiles:
                profile_info = {
                    'path': profile.path.url     # 파일의 경로
                }
                profile_file_info.append(profile_info)

            review['profile_files'] = profile_file_info

            # 리뷰 정보를 review_info에 추가
            review_info['reviews'].append(review)

        # 해당 리뷰 전체 응답
        return Response(review_info)