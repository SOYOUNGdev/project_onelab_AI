import math
from decimal import Decimal

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, F, Q, Sum
from django.http import JsonResponse
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
from place.models import PlaceReview, PlaceLike, PlacePoints
from place.models import Place, PlaceFile
from placeMember.models import PlaceMember
from point.models import Point
from review.models import Review
from school.models import School
from share.models import Share
from oneLabProject.settings import MEDIA_URL
from university.models import University


# 장소글 상세보기 view
class PlaceDetailView(View):
    @transaction.atomic
    def get(self, request, id):
        # id로 해당 게시글 객체 1개 가져와서 post로 선언
        post = Place.objects.get(id=id)

        # 게시글을 작성한 학교 회원 객체 1개 가져와서 school_member로 선언
        school_member = School.objects.get(member=post.school)

        # 상세 페이지 내에 들어갈 작성자의 글
        # 작성자가 현재 게시글(post)의 작성자와 같은 글들 중, 삭제되지 않은 글들만 최신순으로 가져오기
        post_list = Place.enabled_objects.filter(school=school_member).order_by('-id')
        # Paginator를 사용하여 최신글 4개만 가져와서 posts로 선언
        page = request.GET.get('page', 1)
        paginator = Paginator(post_list, 4)
        posts = paginator.page(page)

        # 이미지 파일 가져오기
        # 4개의 장소 하나씩 돌면서
        for p in posts:
            # 해당 장소와 연관된 file 중, 첫 번째 파일만 가져와 first_file로 선언
            first_file = p.placefile_set.first()
            if first_file:
                # 파일이 있으면 파일의 경로를 기반으로 URL 생성
                # 즉, 이미지의 path에 upload경로를 붙인 경로를 image_url로 선언
                p.image_url = f"{MEDIA_URL}{first_file.path}"
            else:
                # 파일이 없다면, None
                p.image_url = None


        # 리뷰 평균과 개수
        # 해당 게시글에 작성된 리뷰 중, 삭제되지 않은 리뷰만 가져와 reviews로 선언
        reviews = PlaceReview.enabled_objects.filter(place_id=post.id)
        # 만약 리뷰가 있다면
        if len(reviews) > 0:
            # 집계함수를 이용 -> 총 개수를 review_count로 선언
            review_count = reviews.count()
            # 각 리뷰들의 별점을 기반으로 aggregate 함수 사용 -> 전체 평균을 구하여 review_avg_decimal로 선언
            review_avg_decimal = reviews.aggregate(avg_rating=Avg('review__review_rating'))['avg_rating']
            # 구한 평균을 소수점 한자리까지 반올림 -> review_avg_rounded로 선언
            review_avg_rounded = Decimal(review_avg_decimal).quantize(Decimal('0.1'))
        # 리뷰가 없다면
        else:
            # 리뷰 개수 = 0
            review_count = 0
            # 리뷰 평균 = 0.0
            review_avg_rounded = 0.0

        # 좋아요 수
        # 좋아요가 되어있는 글들 중, 해당 게시글의 좋아요만 가져오기 -> 집계함수를 사용 -> 해당 게시글의 총 좋아요 수 = place_like_count로 선언
        place_like_count = PlaceLike.objects.filter(place=post).count()

        # 회원이 좋아요를 한 상태인지
        # 로그인 되어있는(session에 저장되어 있는) 회원 객체 1개 가져와 member로 선언
        member = Member.objects.get(id=request.session['member']['id'])
        # 해당 글에 좋아요를 한 placelike 객체 가져와서 place_likes로 선언
        place_likes = PlaceLike.objects.filter(place=post)

        # member가 좋아요를 한 상태인지 결정할 flag를 member_like로 선언, 초기값은 False
        member_like = False
        # place_likes 하나씩 반복
        for place_like in place_likes:
            try:
                # 해당 Like 객체
                # member = 현재 로그인된 회원, like_status = 좋아요를 한 상태(취소시, False로 상태변경됨), id = 해당 place_like객체의 like_id
                like_object = Like.objects.get(member=member, like_status=True, id=place_like.like_id)
                # 해당 Like 객체가 존재
                # 로그인된 회원이 해당 게시글에 좋아요를 한 상태이므로, member_like를 True로 변경
                member_like = True
            # 해당 like 객체가 존재하지 않는다면,
            except Like.DoesNotExist:
                # 좋아요한 상태가 아님
                member_like = False

        # 위에서 가져온 data들을 dict 타입인 context로 선언
        context = {
            'place': post,
            'place_files': list(post.placefile_set.all()),
            'posts': posts,
            'review_count': review_count,
            'review_avg_rounded': review_avg_rounded,
            'place_like_count': place_like_count,
            'member_like': member_like,
        }
        # 상세보기 페이지로 이동하면서 context 함께 전달
        return render(request, 'place/detail.html', context)

    # -------------결제 부분 주석 포함 87번째 줄부터 추가하시면 됩니다!!!--------------------------------------------------#
    def post(self, request, id):
        # post = 해당 장소 공유 아이디
        post = Place.objects.get(id=id)
        # price = 장소의 포인트 가격
        school = post.school_id
        price = post.place_points
        # place_member = 해당 장소를 공유한 학교 회원 아이디
        place_member = post.school_id
        # 이게 필요한가? 이미 위에서 장소의 학교회원 아이디를 받았는데
        place_member_id = School.objects.get(member_id=school)
        # 그냥 디버깅 용으로 선언한 거임
        print(place_member_id)  # --> 1번 아이디의 학교멤버
        # 학교 회원에서 실제 멤버 아이디를 가져옴
        member = place_member_id.member_id  # --> 3번 아이디의 멤버
        # point 모델에 적립(status=3), 가격 , 멤버를 추가함
        Point.objects.create(member_id=member, point_status=3, point=price)
        # 학교회원의 적립 포인트를 출력한다.
        print(Point.objects.filter(member_id=member, point_status=3).aggregate(Sum('point'))['point__sum'])
        # 구매하려는 대학생 회원 아이디를 가져온다.
        member_id = request.session['member']['id']
        print(member_id)
        university = University.objects.get(member_id=member_id)
        print(university)
        # 장소대여 포인트 모델 을 불러온다.
        place_price = PlacePoints.objects.filter(place_id=post.id)
        # 실제 대학생의 포인트에서 장소대여 포인트 값이 빠져야함
        university.university_member_points -= price
        # 적용된 값 저장
        university.save()

        # 장소대여의 결제 status가 1로 바뀐다.
        place = Place.objects.update(place_order_status=1)

        # point 모델에 사용된 포인트 정보를 추가한다.
        datas = {
            'point': price,
            'point_status': 2,
            'member_id': member_id
        }
        point = Point.objects.create(**datas)
        # place point 모델에 정보를 추가한다. (이미 구매한 사용자면 조회)
        place_data = {
            'place_id': id,
            'points_id': point.id
        }
        PlacePoints.objects.get_or_create(**place_data)
        # ------------------------------결제 부분 완료---------------------------------#
        # --------------------------------멤버 참여 기능 시작---------------------------#
        join_data = {
            'place_member_status': 0,
            'university_id': request.session['member']['id'],
            'place_id': post.id
        }
        PlaceMember.objects.get_or_create(**join_data)
        # --------------------------------멤버 참여 기능 완료---------------------------#
        return redirect('/myPage/main/')


# 좋아요를 누를 때마다 들어오는 View
class PlaceLikeView(View):
    @transaction.atomic
    def post(self, request):
        # 요청 방식이 post이고, ajax라면
        if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # JSON 데이터 파싱
            data = json.loads(request.body)
            # body에 있는 place_id 가져와서 place_id로 선언
            place_id = data.get('place_id')
            # 해당 place_id 가진 게시글 가져와서 place로 선언
            place = Place.objects.get(id=place_id)
            # 세션에 들어있는 회원 객체 member로 선언
            member = Member.objects.get(id=request.session['member']['id'])

            try:
                # 해당 회원이 이 게시글에 대해 좋아요를 한 경우
                place_like = PlaceLike.objects.get(place=place, like__member=member)
                if place_like.like.like_status:
                    # 이미 좋아요한 경우, 좋아요 취소
                    place_like.like.like_status = False
                    place_like.like.save()  # like_status를 False로 변경
                    place_like.delete()  # 좋아요 삭제
                else:
                    # 이미 좋아요를 취소한 경우
                    # like_status를 True로 변경하여 다시 좋아요를 한 것으로 처리
                    place_like.like.like_status = True
                    place_like.like.save()  # like_status를 True로 변경
            except PlaceLike.DoesNotExist:
                # 해당 회원이 이 게시글에 대해 좋아요를 하지 않은 경우
                # 좋아요 생성
                like = Like.objects.create(member=member, like_status=True)
                place_like = PlaceLike.objects.create(place=place, like=like)

            # 업데이트된 좋아요 수 응답
            place_like_count = PlaceLike.objects.filter(place=place).count()
            return JsonResponse({'like_count': place_like_count})

        # AJAX 요청이 아닌 경우, 상세보기 페이지로 이동
        return render(request, 'place/detail.html')

# 장소 공유 글 작성할 때 view
class PlaceWriteView(View):
    # 작성 페이지로 이동할 때
    @transaction.atomic
    def get(self, request):
        # 로그인 되어있는 회원 객체 -> member로 선언
        member = Member.objects.get(id=request.session['member']['id'])
        # 학교 회원만 장소공유 글을 작성할 수 있음
        # member객체가 member인 학교 회원 객체 1개 가져와 school_member로 선언
        school_member = School.objects.get(member=member)

        # 마이 포인트 계산
        # member=member이고 point_status=3인 point객체가 있다면
        if len(list(Point.objects.filter(member=member, point_status=3))) > 0:
            # Sum과 aggregate함수를 이용하여 해당 포인트들의 합을 구한 뒤, point로 선언
            point = Point.objects.filter(member=member, point_status=3).aggregate(Sum('point'))['point__sum']
        else:
            # 로그인 한 회원의 포인트 내역이 없다면, insert
            point = Point.objects.create(member=member, point_status=3)

        # 마이 포스트 수
        # 로그인 한 회원이 작성한 장소글들의 제목과 id만 가져오기
        places = Place.enabled_objects.filter(school=school_member).values('place_title', 'id')
        # 집계함수 이용하여 총 개수 계산 -> total_post_count로 선언
        total_post_count = places.count()

        # 위에서 가져온 데이터들 data에 dict 타입으로 저장
        data = {
            'point': point,
            'total_post_count': total_post_count,
            'places': places,
        }
        # 글 작성 페이지 이동, data함께 전달
        return render(request, 'place/write.html', data)

    @transaction.atomic
    def post(self, request):
        # 회면에서 post로 받아온 데이터를 data에 저장
        data = request.POST
        # input 태그 하나에 여러 파일일 때(multiple), getlist('{input태그 name값}')
        # 파일이 여러개 이므로 getlist로 가져와서 files에 따로 저장
        files = request.FILES.getlist('upload-file')

        # input 태그 하나 당 파일 1개 일 떄
        # file = request.FILES

        # 로그인 되어있는 회원 -> member
        member = Member.objects.get(id=request.session['member']['id'])
        # 그 회원이 학교회원(School 객체)이므로, school_member로 선언
        school_member = School.objects.get(member=member)

        # 위에서 받아온 data의 name을 사용하여 맞는 데이터들을 dict타입의 data로 선언
        data = {
            'place_title': data['place-title'],
            'place_points': data['place-points'],
            'place_date': data['place-date'],
            'place_content': data['place-content'],
            'place_ask_email': data['place-ask-email'],
            'place_url': data['place-url'],
            'school': school_member
        }

        # 작성 된 글 insert
        place = Place.objects.create(**data)

        # 가져온 파일들 하나씩 반복
        for file in files:
            # 업로드된 파일을 File 모델에 저장
            file_instance = File.objects.create(file_size=file.size)
            # 만든 파일 객체를 PlaceLike 모델에 저장
            PlaceFile.objects.create(place=place, file=file_instance, path=file)

        # 작성한 게시글의 상세보기 페이지로 이동
        return redirect(reverse('place:detail', kwargs={'id': place.id}))

# 수정하기 시에 들어오는 view
class PlaceUpdateView(View):
    # 글 수정하기 페이지 들어올 때, 해당 게시글의 id함께 받아옴
    @transaction.atomic
    def get(self, request, id):
        # 로그인 된 회원 -> member -> school_member
        member = Member.objects.get(id=request.session['member']['id'])
        school_member = School.objects.get(member=member)

        # 마이 포인트 계산
        # member=member이고 point_status=3인 point객체가 있다면
        if len(list(Point.objects.filter(member=member, point_status=3))) > 0:
            # Sum과 aggregate함수를 이용하여 해당 포인트들의 합을 구한 뒤, point로 선언
            point = Point.objects.filter(member=member, point_status=3).aggregate(Sum('point'))['point__sum']
        else:
            # 로그인 한 회원의 포인트 내역이 없다면, insert
            point = Point.objects.create(member=member, point_status=3)

        # 마이 포스트 수
        # 로그인 한 회원이 작성한 장소글들의 제목과 id만 가져오기
        places = Place.enabled_objects.filter(school=school_member).values('place_title', 'id')
        # 집계함수 이용하여 총 개수 계산 -> total_post_count로 선언
        total_post_count = places.count()

        # 전달받은 id이용 -> 수정하는 place객체 가져와서 post로 선언
        post = Place.objects.get(id=id)
        # update_url 생성
        update_url = reverse('place:update', args=[id])
        # 게시글 내용 중에 앞뒤 공백이 있는 경우, 자르기
        place_content = post.place_content.strip()
        # 위에서 가져온 데이터들 dict 타입으로 context에 저장
        context = {
            'place': post,
            'place_content': place_content,
            'place_files': list(post.placefile_set.all()),
            'update_url': update_url,
            'point': point,
            'total_post_count': total_post_count,
        }
        # 수정하기 페이지로 이동, context함께 전달
        return render(request, 'place/update.html', context)

    # 수정 완료 시
    @transaction.atomic()
    def post(self, request, id):
        # post방식으로 받아온 데이터들 data로 선언
        data = request.POST
        # 기존의 Place 객체 가져오기
        place = Place.objects.get(id=id)

        # 가져온 name값으로 가져온 데이터들 모두 update하기
        place.place_title = data['place-title']
        place.place_content = data['place-content']
        place.place_ask_email = data['place-ask-email']
        place.place_url = data['place-url']
        place.place_date = data['place-date']
        place.place_points = data['place-points']
        place.save(update_fields=['place_title', 'place_content', 'place_ask_email', 'place_url', 'place_date',
                                  'place_points'])

        # 새로운 파일들이 있는지 확인
        files = request.FILES.getlist('upload-file')

        # 새로운 파일들이 없는 경우 기존 파일들 유지
        if not files:
            # 수정된 Place의 상세 페이지로 이동
            return redirect(place.get_absolute_url())

        # 기존의 파일들 모두 삭제
        place.placefile_set.all().delete()

        # 새로운 파일들 처리
        for file in files:
            # 파일 저장
            file_instance = File.objects.create(file_size=file.size)
            PlaceFile.objects.create(place=place, file=file_instance, path=file)

        # 수정된 place 글의 상세 페이지로 이동
        return redirect(place.get_absolute_url())

# 삭제하기 view
class PlaceDeleteView(View):
    def get(self, request):
        # 해당 게시글 soft_delete 방식으로 post_status를 False로 update
        place_id = request.GET['id']
        Place.objects.filter(id=place_id).update(place_post_status=False)
        # 삭제 후에는 리스트 페이지로 이동
        return redirect('/place/list')

# 리뷰리스트 view
class PlaceReviewListView(View):
    # 리뷰 페이지 아동 시
    def get(self, request):
        # URL에서 전달된 ID 값 가져오기
        place_id = request.GET.get('place_id')
        # 가져온 ID를 이용하여 해당하는 게시글 -> post로 선언
        post = Place.objects.get(id=place_id)
        # 좋아요 수 -> place_like_count로 선언
        place_like_count = PlaceLike.objects.filter(place=post).count()
        # 페이지 이동 시, 함께 전달해야할 데이터들 post_data에 dict타입으로 저장
        post_data = {
            'place_id': post.id,
            'place_title': post.place_title,
            'place_points': post.place_points,
            'place_date': post.place_date,
            'place_content': post.place_content,
            'place_ask_email': post.place_ask_email,
            'place_url': post.place_url,
            'school_member_address': post.school.school_member_address,
            'school_name': post.school.school_name,
            'member_name': post.school.member.member_name,
            'member_email': post.school.member.member_email,
            'place_files': post.placefile_set.all(),
            'place_like_count': place_like_count,
        }

        # 리뷰 페이지로 이동, post_data 함께 전달
        return render(request, 'place/review.html', post_data)

# rest방식의 리뷰리스트 view
class PlaceReviewListAPIView(APIView):
    # 게시글 id와 page 함께 받음
    @transaction.atomic
    def get(self, request, place_id, page):
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
            reviews = PlaceReview.enabled_objects.filter(place_id=place_id).annotate(member_name=F('review__member__member_name'))\
                      .values(*datas).order_by('-review__review_rating', '-review__created_date')[offset:limit]
        # 전달받은 정렬 방식이 별점 낮은 순일 경우
        elif sort == 'lowest_rating':
            reviews = PlaceReview.enabled_objects.filter(place_id=place_id).annotate(member_name=F('review__member__member_name'))\
                      .values(*datas).order_by('review__review_rating', '-review__created_date')[offset:limit]
        # 전달받은 정렬 방식이 최신순일 경우
        else:
            reviews = PlaceReview.enabled_objects.filter(place_id=place_id).annotate(member_name=F('review__member__member_name'))\
                      .values(*datas).order_by('-review__created_date')[offset:limit]

        # 리뷰 개수 가져오기
        total_review_count = PlaceReview.enabled_objects.filter(place_id=place_id).count()

        # 리뷰가 없을 때 처리
        if total_review_count == 0:
            return Response({
                'reviews': [], 'hasNext': False, 'place_id': place_id, 'review_count': 0.0, 'review_avg': 0.0
            })

        # 리뷰 평균
        review_avg_decimal = \
        PlaceReview.enabled_objects.filter(place_id=place_id).aggregate(avg_rating=Avg('review__review_rating'))['avg_rating']
        review_avg_rounded = Decimal(review_avg_decimal).quantize(Decimal('0.1'))  # 수정

        # 다음 페이지가 있는지 계산할 때도 전체 리뷰 개수를 사용하여 계산
        has_next = total_review_count > offset + limit

        review_info = {
            'reviews': [],
            'hasNext': has_next,
            'place_id': place_id,
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

            # 멤버 프로필 이미지를 리스트에 추가
            profile_file_info = []
            for profile in member_profiles:
                profile_info = {
                    'path': profile.path.url    # 파일의 경로
                }
                profile_file_info.append(profile_info)

            review['profile_files'] = profile_file_info

            # 리뷰 정보를 review_info에 추가
            review_info['reviews'].append(review)

        # 해당 리뷰 전체 응답
        return Response(review_info)

# 게시글 리스트 view
class PlaceListView(View):
    def get(self, request):
        # 집계함수를 이용 -> 총 게시글 수 place_total_count로 선언
        place_total_count = Place.enabled_objects.all().count()
        # data에 dict타입으로 담기
        data = {'place_total_count': place_total_count}
        # 리스트 페이지로 이동, data함께 전달
        return render(request, 'place/list.html', data)

# rest방식의 리스트 view
class PlaceListAPIView(APIView):
    @transaction.atomic
    def get(self, request, page):
        # 한 페이지에 보여줄 장소의 개수와 페이지
        row_count = 9

        # 시작 번호 -> offset
        offset = (page - 1) * row_count
        # 끝 번호 -> limit
        limit = page * row_count

        # 가져올 데이터들 먼저 리스트에 담기
        datas = [
            'id',
            'place_title',
            'place_points',
            'place_address',
            'university_name',
            'place_date',
        ]

        # 지역 필터
        # default는 전체 지역
        area_sort = request.GET.get('areaSort', 'all')
        # 전체 지역일 경우
        if area_sort == 'all':
            # 모든 게시글 불러오기
            places = Place.enabled_objects.all()
        else:
            # 해당 지역에 속한 학교 가져오기
            # strip = 공백 제거
            places = Place.enabled_objects.filter(school__school_member_address__contains=area_sort.strip())

        # 선택된 지역에 따라 필터링된 장소 목록 가져오기(최신순)
        # 학교 주소와 이름은 별칭으로 지정
        places = places.annotate(place_address=F('school__school_member_address'),\
                                 university_name=F('school__school_name'))\
                                .values(*datas).order_by('-id')
        # 필터링 이후, 게시글 총 개수를 집계함수 이용하여 place_count에 저장
        place_count = places.count()
        # 시작~끝에 해당되는 게시글만 가져오기
        places = places[offset:limit]
        # 다음 페이지가 있는지 계산
        has_next = place_count > offset + limit

        # 회원이 좋아요를 한 상태인지
        # 로그인 된 회원 객체 -> member
        member = Member.objects.get(id=request.session['member']['id'])

        # response할 데이터 담기
        place_info = {
            'places': [],
            'member_like': {},
        }

        # 장소 하나씩 반복
        for place in places:
            # 장소의 id
            place_one_id = place['id']
            # 장소의 id이용하여 글 객체 1개 가져오기 -> place_one
            place_one = Place.objects.get(id=place_one_id)
            # 장소글과 연관된 파일들 가져오기 -> place_files
            place_files = place_one.placefile_set.all()

            # 장소공유 파일 데이터를 리스트에 추가
            place_file_info = []
            for file in place_files:
                file_info = {
                    'id': file.pk,
                    'path': file.path.url,  # 파일의 경로
                }
                place_file_info.append(file_info)

            # 장소 정보에 파일 정보를 추가
            place['place_files'] = place_file_info

            # 해당 장소에 대한 회원의 좋아요 여부 확인
            try:
                like_object = PlaceLike.objects.get(like__member=member, like__like_status=True, place=place_one)
                place_info['member_like'][place_one_id] = True
            except PlaceLike.DoesNotExist:
                place_info['member_like'][place_one_id] = False

            place_info['places'].append(place)

        # 장소 데이터 응답
        return Response(place_info)