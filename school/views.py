from django.shortcuts import render
from django.views import View

from member.models import Member
from school.models import School

# 학교 메인페이지 view
class SchoolMainView(View):
    def get(self, request):
        # 로그인된 회원 -> member
        member = request.session['member']['id']
        # 승인된 학교 회원일 경우
        if School.objects.filter(member=member, school_member_status=1).exists():
            # session에 school_member_check를 true로 저장
            request.session['school_member_check'] = True
        # 아닐 경우
        else:
            # session에 school_member_check를 false로 저장
            request.session['school_member_check'] = False

        # 메인페이지 이동
        return render(request, 'school/main.html')

# 학교 회원 신청 view
class SchoolMemberView(View):
    def post(self, request):
        # 로그인된 회원 -> member
        member = Member.objects.get(id=request.session['member']['id'])
        # post로 전달된 data
        data = request.POST

        # 받아온 data -> name값 이용하여 context에 dict 타입으로 저장
        context = {
            'school_name': data['school-name'],
            'school_member_address': data['school-input-address'],
        }
        # school객체 생성
        # status = 0으로
        School.objects.create(member=member, **context)
        
        # 메인페이지 이동
        return render(request,'school/main.html')


