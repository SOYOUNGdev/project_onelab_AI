from django.db import transaction
from django.shortcuts import render, redirect
from django.views import View

from file.models import File
from member.models import Member
from place.models import PlaceReview, Place
from review.models import Review, ReviewFile
from share.models import Share, ShareReview


# 장소공유글 후기 view
class ReviewPlaceWriteView(View):
    # 후기 작성 페이지로 이동할 때
    def get(self, request):
        # id값을 받아서 place객체 가져오기
        place = Place.objects.get(id=request.GET['id'])
        # place-write페이지로 이동, place 함께 전달
        return render(request, 'review/place-write.html', {'place': place})

    # 후기 작성 완료 시
    @transaction.atomic
    def post(self, request):
        # post로 요청된 데이터
        data = request.POST
        # 장소글의 id를 받아 place_id로 선언
        place_id = data["place-id"]

        # input 태그 하나 당 파일 1개 일 떄
        # 파일 받아서 file로 선언
        file = request.FILES
        # 세션에 저장된 로그인 된 회원 -> member
        member = Member.objects.get(id=request.session['member']['id'])

        # 받아온 데이터 -> name값 이용하여 data에 dict타입으로 저장
        data = {
            'review_content': data['review-content'],
            'review_rating': data['review-rating'],
            'member': member,
        }
        # review insert
        review = Review.objects.create(**data)

        # file insert
        for key, file in file.items():
            # file 생성
            file_instance = File.objects.create(file_size=file.size)
            # reviewfile 생성
            ReviewFile.objects.create(review=review, file=file_instance, path=file)

        # id를 이용하여 place객체 1개 가져오기
        place = Place.objects.get(id=place_id)
        # 리뷰와 장소 정보 dict로 담아 -> place_review_info로 선언
        place_review_info = {
            'review': review,
            'place': place
        }
        # PlaceReview 생성
        PlaceReview.objects.create(**place_review_info)

        # 리뷰 페이지로 이동(qurey string을 사용)
        return redirect(f'/place/review/list?place_id={place_id}')


# 자료 공유글 후기
class ReviewShareWriteView(View):
    # 후기 작성 페이지로 이동할 때
    def get(self, request):
        # id값을 받아서 share객체 가져오기
        share = Share.objects.get(id=request.GET['id'])
        # share-write페이지로 이동, share 함께 전달
        return render(request, 'review/share-write.html', {'share': share})

    # 후기 작성 완료 시
    @transaction.atomic
    def post(self, request):
        # post로 요청된 데이터
        data = request.POST
        # 자료글의 id를 받아 share_id로 선언
        share_id = data["share-id"]

        # input 태그 하나 당 파일 1개 일 떄
        # 파일 받아서 file로 선언
        file = request.FILES
        # 세션에 저장된 로그인 된 회원 -> member
        member = Member.objects.get(id=request.session['member']['id'])

        # 받아온 데이터 -> name값 이용하여 data에 dict타입으로 저장
        data = {
            'review_content': data['review-content'],
            'review_rating': data['review-rating'],
            'member': member,
        }
        # review insert
        review = Review.objects.create(**data)

        # file insert
        for key, file in file.items():
            # file 생성
            file_instance = File.objects.create(file_size=file.size)
            # reviewfile 생성
            ReviewFile.objects.create(review=review, file=file_instance, path=file)

        # id를 이용하여 share객체 1개 가져오기
        share = Share.objects.get(id=share_id)
        # 리뷰와 자료 정보 dict로 담아 -> share_review_info로 선언
        share_review_info = {
            'review': review,
            'share': share
        }
        # shareReview 생성
        ShareReview.objects.create(**share_review_info)

        # 리뷰 페이지로 이동(qurey string을 사용)
        return redirect(f'/share/review/list?share_id={share_id}')


