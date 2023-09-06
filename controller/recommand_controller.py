from flask import render_template, Blueprint,  request
from sqlalchemy import create_engine, text
import pymysql
import json


bp = Blueprint('reco',
               __name__,
               url_prefix='/reco')



# 요청 URL : http://127.0.0.1:8888/reco/resume
# @bp.route('/re',methods = ['GET'])# 두개일땐 ('GET','POST')
# def re():
#     url = "http://api.data.go.kr/openapi/tn_pubr_public_ovrspd_prvn_manage_api?serviceKey=개인인증키&pageNo=1&numOfRows=1000&type=json"
#     response = requests.get(url)
#     contents = response.text
#     #pp = pprint.PrettyPrinter(indent=4)
#     print(contents)


@bp.route('/test',methods = ['GET'])
def test():
    return "test Success!"
    
    
@bp.route('/info',methods = ['GET'])
def info():

    #안드로이드 -> email
    # 우재가 배포해줌 수정하면 됨. 
    import pandas as pd
    reco_db = pymysql.connect(
        user='root',
        passwd='mysql1234',
        host='-',
        db='recommand',
        port=3306,
        charset='utf8'
    )
    member_id = request.get_json()
    id = member_id['id']

    cursor = reco_db.cursor(pymysql.cursors.DictCursor)


    query1 = "SELECT * FROM `members` WHERE email = %s"
    cursor.execute(query1, (id,))
    mem = cursor.fetchall()


    mem = pd.DataFrame(mem)
    print(mem) # 나이, 거주지 1(띄어쓰기로 경북 / **시 파싱) , 거주지 2(홍화루 .. ), email, 장애유형 및 등급, 이름

    # email, member_id는 그대로
    mem.rename(columns = {'address_details' : '거주지_상세', 'address_info': '거주지_대분류', 'age' : '나이', 'disability_type' : '장애유형_등급' , 'username' : '이름'},inplace = True)

    sql1 = "select * from `employment_information`;"
    cursor.execute(sql1)
    employ_info = cursor.fetchall()
    df = pd.DataFrame(employ_info)
    df.rename(columns={'id': '연번', 'age': '연령', 'disability_type': '장애유형', 'employment_date': '취업유형',
                       'job_category': '취업직종대분류', 'severity': '중증여부', 'work_region': '근무지역'}, inplace=True)

    #print(mem)
    mem['장애유형'] = mem['장애유형_등급'].str.split('_').str.get(0)
    mem['장애등급'] = mem['장애유형_등급'].str.split('_').str.get(1)

    # 같은 장애를 가진 구직자의 정보에 의해,(20대는 ~  @@님은 "---" 직종에 합격할 확률이 높아요!(장애유형, 중증여부, 연령)


    in_enable = mem['장애유형'].values[0]
    in_grade = mem['장애등급'].values[0]
    in_age = mem['나이'].values[0]
    #in_age = int(in_age)
    cond1 = df.loc[df['장애유형'] == in_enable]
    cond2 = cond1.loc[cond1['중증여부'] == in_grade]
    cond3 = cond2.loc[(cond2['연령']>=((in_age//10)*10)) & (cond2['연령']<((in_age//10 + 1)*10))]
    a = cond3['취업직종대분류'].value_counts(ascending = False).index.values[0]
    #a.to_json(orient='records', force_ascii=False, indent=4)
    ## json 형태로 보내기

    return a

@bp.route('/wish',methods = ['GET'])
def wish():
    import pandas as pd
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    import pandas as pd
    reco_db = pymysql.connect(
        user='root',
        passwd='mysql1234',
        host='-',
        db='recommand',
        port=3306,
        charset='utf8'
    )
    member_id = request.get_json()
    id = member_id['id']

    cursor = reco_db.cursor(pymysql.cursors.DictCursor)

    query = "select * from `job_announcement`;"
    cursor.execute(query)
    emp_data = cursor.fetchall()
    emp_data = pd.DataFrame(emp_data)
    emp_data.rename(columns={'job_announcement_id': '연번', 'application_date': '구인신청일자', 'business_address': '사업장주소',
                             'company_name': '사업장명', 'company_type': '기업형태', 'contact_number': '연락처',
                             'entry_form': '입사형태', 'form_of_wages': '임금형태', 'major_field': '전공계열',
                             'recruitment_period': '모집기간',
                             'recruitment_type': '모집직종', 'registration_date': '등록일', 'required_credentials': '요구자격증',
                             'required_education': '요구학력', 'required_experience': '요구경력', 'responsible_agency': '담당기관',
                             'type_of_employment': '고용형태', 'wage': '임금'}, inplace=True)


    ## 처음에 아래 3개 모두 가져오고 프레임 생성
    ## m
    query1 = '''
        SELECT members.member_id, members.username ,members.email, member_wishlist.job_announcement_id
        FROM members
        JOIN member_wishlist ON members.member_id = member_wishlist.member_id
        
    '''
    # WHERE members.email = % s

    cursor.execute(query1)
    #전체 위시리스트가 들어가있는 dataframe
    mem_wish = cursor.fetchall()
    mem_wish = pd.DataFrame(mem_wish)


    # email, member_id는 그대로
    mem_wish.rename(
        columns={'job_announcement_id': 'Basket','username': 'User'}, inplace=True)

    # 값 리스트 형태로 변경

    #[mem_wish['email'] == id]
    mem = mem_wish.groupby('User')['Basket'].agg(list).reset_index()
    user = mem[['User','Basket']]


    # user = pd.DataFrame({'User': ['JJS', 'KGB', 'JWJ', 'PJS'],
    #                      'Basket': [[63, 274, 289], [289, 406, 598], [858, 63], [858, 158, 288]]})
    #
    # user = pd.DataFrame({
    #     'User': ['JJS', 'KGB', 'JWJ', 'PJS', 'dd', 'ss', 'ww'],
    #     'Basket': [[1, 2, 3, 4],
    #                [1, 2, 3, 4, 5, 6],
    #                [858, 63],
    #                [858, 158, 288],
    #                [1, 2, 3, 8],
    #                [1, 2, 3, 4, 10],
    #                [1, 2, 10, 4, 9]]
    # })

    items = set()
    for basket in user['Basket']:
        items.update(basket)

    num_items = len(items)

    item_index = {item: index for index, item in enumerate(items)}

    user_item_matrix = np.zeros((len(user), num_items))
    for i, basket in enumerate(user['Basket']):
        for item in basket:
            item_idx = item_index[item]
            user_item_matrix[i, item_idx] = 1

    similarity_matrix = cosine_similarity(user_item_matrix)

    target_user = mem_wish.loc[mem_wish['email'] == id,'User'].values[0]#'JJS'
    target_user_index = user[user['User'] == target_user].index[0]

    similar_users = np.where(similarity_matrix[target_user_index] >= 0.65)[0]
    similar_users = similar_users[similar_users != target_user_index]

    recommendations = []
    for user_idx in similar_users:
        basket = user.loc[user_idx, 'Basket']
        for item in basket:
            if item not in user.loc[target_user_index, 'Basket'] and item not in recommendations:
                recommendations.append(item)

    res_df = pd.DataFrame()
    for i in recommendations:
        print(i)
        data = emp_data.loc[emp_data['연번'] == i]
        res_df = pd.concat([res_df, data])

    res = res_df.to_json(orient='records', force_ascii=False, indent=4)

    return res
@bp.route('/resume',methods = ['GET'])# 두개일땐 ('GET','POST')
def reco_based_resume():
    # -*- coding: utf-8 -*-
    import pandas as pd
    import numpy as np


    reco_db = pymysql.connect(
        user='root',
        passwd='mysql1234',
        host='-',
        db='recommand',
        port=3306,
        charset='utf8'
    )

    member_id = request.get_json()
    id = member_id['id']

    cursor = reco_db.cursor(pymysql.cursors.DictCursor)
    sql = "select * from `barrier_free_certified_workplace`;"
    sql2 = "select * from `employment_information`;"
    sql3 = "select * from `job_announcement`;"
    sql4 = "select * from `members`;"
    sql5 = "select * from `risk_assessment_certified_workplace`;"
    sql6 = "SELECT resumes.*, members.username FROM `resumes` JOIN members ON resumes.member_id = members.member_id WHERE members.email = %s;"
#---님께 추천된 공고는 ~ 입니다.
    # query1 = '''
    #     SELECT members.member_id, members.username ,members.email, member_wishlist.job_announcement_id
    #     FROM members
    #     JOIN member_wishlist ON members.member_id = member_wishlist.member_id
    #
    # '''
    #
    # query1 = '''
    #     SELECT resumes.id, t1.column2, t2.column3
    #     FROM table1 t1
    #     JOIN table2 t2 ON t1.id = t2.id
    #     WHERE members.email = %s
    # '''


    query = "SELECT * FROM `members` WHERE email = %s"
    cursor.execute(query, (id,))
    mem = cursor.fetchall()

    mem = pd.DataFrame(mem)
    print(mem)

    cursor.execute(sql)
    result = cursor.fetchall()

    cursor.execute(sql2)
    employ_info = cursor.fetchall()

    cursor.execute(sql3)
    emp_data = cursor.fetchall()

    cursor.execute(sql4)
    members = cursor.fetchall()

    cursor.execute(sql5)
    safe = cursor.fetchall()

    cursor.execute(sql6,(id,))
    resumes = cursor.fetchall()



    barrier = pd.DataFrame(result)
    df = pd.DataFrame(employ_info)
    emp_data = pd.DataFrame(emp_data)
    safe = pd.DataFrame(safe)
    members =pd.DataFrame(members)
    resumes = pd.DataFrame(resumes)
    print(resumes)
    print(safe.columns)

    barrier.rename(columns={'id' : '연번','certification_cancellation_status':'인증만료(취소여부)','facility_name' : '시설물명','target':'인증대상','certification_type':'인증구분','grade' : '등급','region_code' : '지역코드','city':'시군구','certification_issued_date' : '인증발급일','certification_expiration_date' : '인증만료일','workplace_type' : '사업장구분'},inplace = True)
    df.rename(columns={'id':'연번','age' : '연령','disability_type' : '장애유형', 'employment_date' : '취업유형','job_category' : '취업직종대분류','severity' : '중증여부','work_region':'근무지역'},inplace = True)
    emp_data.rename(columns = {'job_announcement_id':'연번','application_date':'구인신청일자','business_address' : '사업장주소','company_name' : '사업장명','company_type' : '기업형태','contact_number' : '연락처','entry_form' : '입사형태','form_of_wages': '임금형태','major_field' : '전공계열','recruitment_period' : '모집기간',
                               'recruitment_type' : '모집직종','registration_date': '등록일','required_credentials' : '요구자격증', 'required_education' : '요구학력','required_experience' : '요구경력','responsible_agency':'담당기관','type_of_employment' : '고용형태','wage' : '임금'},inplace= True)
    safe.rename(columns = {'id' : '연번', 'business_name' : '사업장명','district_office_name' : '노동지청명', 'name_of_construction_site' : '공사장명','recognition_date' : '인정일'},inplace = True)
    resumes.rename(columns={'prefer_keyword':'선호기업조건', 'education' : '학력', 'major' : '전공계열', 'prefer_income' : '선호임금' },inplace = True) #
    print(resumes)


    # 한국장애인고용공단_장애물 없는 생활환경(Barrier Free) 인증 시설 정보_20211231.CSV
    ##
    # barrier = pd.read_csv(
    #     'C:/recommendation_server/data_csv/한국장애인고용공단_장애물 없는 생활환경(Barrier Free) 인증 시설 정보_20211231.CSV',
    #     encoding='cp949')
    # barrier


    ##
    import pandas as pd
    emp_data = pd.read_csv('C:/recommendation_server/data_csv/한국장애인고용공단_장애인 구인 정보_20230512.CSV', encoding='cp949')
    emp_data_ori = emp_data.copy()


##(수정) 데이터베이스에서 기업선호조건 받아오기
    important = []
    important.append(resumes['선호기업조건'].values[0])
    print(important)
    # for i in range(3):
    #     n = input('컬럼에 들어갈 입력값들')
    #
    #     # i로 대체
    #     important.append(n)
    not_important = pd.DataFrame()
##(수정) 직종 대분류, 중분류 분류
    job_m = '경영·행정·사무직'
    job_s = '사무 보조원(공공기관)'
    job_m = job_m.replace('·', '_')

    df['취업직종대분류'] = df['취업직종대분류'].str.replace('·', '_')
    df['취업직종대분류'] = df['취업직종대분류'].str.replace(' ', '_')
    df['취업직종대분류'] = df['취업직종대분류'].str.replace('(', '_')
    df['취업직종대분류'] = df['취업직종대분류'].str.replace(')', '_')

    job_main_list = {
        '경영_행정_사무직': ['데스크 안내원', '통계·설문 조사원(슈퍼바이저 포함)', '인사·노무 전문가', '전산자료 입력원(DB·단순자료)', '고객 상담원(A/S·고장·제품사용)',
                      '마케팅 전문가', '모니터 요원', '사무 보조원(공공기관)', '사무 보조원(일반사업체)', '총무 및 일반 사무원', '인사 사무원', '경영 기획 사무원',
                      '마케팅·광고·홍보·상품기획 사무원', '공공행정 사무원', '물류 사무원(물류 관리사)', '생산·품질 사무원 및 관리원(전기·전자·컴퓨터)', '교육·훈련 사무원',
                      '생산·품질 사무원 및 관리원(음식료품)', '경리 사무원(일반사업체)', '학교행정 사무원(교무)', '회계 사무원(일반 사업체)', '재무 사무원', '조세행정 사무원',
                      '영업 기획·관리·지원 사무원', '국가·지방행정 사무원', '생산·품질 사무원 및 관리원(그 외 분야)', '단순 경리 사무원']
        , '운전_운송직': ['신문·음료(우유·요구르트 등) 기타 배달원', '일반 택배원(퀵서비스 포함)', '우편물 집배원', '하역·적재 종사원', '경·소형 화물차 운전원',
                     '배송·납품 운전원(납품영업 포함)', '노선버스 운전원(시내, 마을, 시외, 고속)', '승용차 운전원(자가용 운전원)', '관광 및 통근·통학·학원 및 기타 버스 운전원']
        , '기계_설치정비_생산직': ['기계·금속 분야 단순 종사원', 'CNC 밀링기 조작원(NC 밀링기 조작원)', '물펌프·정수 처리장치 조작원', '펄프·종이 제조장치 조작원',
                          '신발 제조기계 조작원 및 조립원', '주입·포장·상표부착기 등 기타 기계 조작원', '두부 및 유사제품 생산기계 조작원', '세탁 기계 조작원',
                          '기타 비금속제품 생산기계 조작원', '육류 가공기계 조작원', '종이제품 생산기계 조작원', '자동차 부분품 조립·검사원', '자동차 조립·검사원',
                          '기타 기계 조립·검사원']
        , '금속_재료_설치_정비_생산직_판금_단조_주조_용접_도장_등_': ['금속기계부품 조립원', '기타 금속공작기계 조작원 및 보조원']
        , '화학_환경_설치_정비_생산직': ['화학·환경·에너지 분야 단순 종사원', '플라스틱 사출성형기 조작원', '플라스틱제품 조립원 및 검사원', 'LCD 부품·제품 조립·검사원',
                              '고무제품 조립원 및 검사원']
        , '전기_전자_설치_정비_생산직': ['사무용 전자기기 설치·수리원(컴퓨터 제외)', '전기 부품·제품 생산기계 조작원', '기타 전기·전자 설비 조작원', '전자 부품·제품 생산기계 조작원',
                              'LED 부품·제품 조립·검사원', '기타 전자 부품·제품 조립·검사원', '전기 부품·제품 조립·검사원', '전기·전자 분야 단순 종사원']
        , '제조_연구개발직_및_공학기술직': ['산업 안전원 및 위험물 관리원', '전기·전자 장비 제도사(캐드원)', '기타 제도사(캐드원) ', '기계·금속 제도사(캐드원)']
        , '섬유_의복_생산직': ['의복·직물 검사 등 기타 섬유·가죽 기능원', '양장·양복 제조원', '섬유·의복 분야 단순 종사원', '재단사', '재봉사(의류·직물) ',
                        '섬유가공 준비 및 후가공 처리원']
        , '제조_단순직': ['제조 단순 종사원']
        , '정보통신_설치_정비직': ['통신장비 설치·수리원']
        , '인쇄_목재_공예_및_기타_설치_정비_생산직': ['인쇄 후가공원', '인쇄판·인쇄필름 출력원', '인쇄, 목재, 가구 및 기타 제조 분야 단순 종사원']
        , '식품_가공_생산직': ['식품 분야 단순 종사원', '김치·밑반찬 제조 종사원', '떡 제조원(한과 포함)', '제과·제빵원', '기타 식품가공 종사원']
        , '교육직': ['디자인·캐드 강사', '기타 교사', '간호조무사, 간병, 관광안내 강사', '학습지·교육교구 방문 강사', '교육연수기관 및 기업체내 강사(리더십, 서비스마인드 등)',
                  '프로그래밍·웹·웹디자인·DB 강사', '컴퓨터 기초 강사(OA, 워드, 엑셀, 컴퓨터활용능력 등)']
        , '금융_보험직': ['은행 사무원(출납창구 제외)', '카드사·신협·새마을금고·할부사, 우체국(금융부문) 등 기타 사무원']
        , '예술_디자인_방송직': ['화가 및 조각가', '지휘자, 작곡가 및 연주가', '조련사(공연)·마술사 등 기타 시각 및 공연 예술가',
                         '엑스트라,소품·무대의상 관리 등 기타 연극·영화·방송 종사원']
        , '음식_서비스직': ['일반 음식점 서빙원', '패스트푸드 준비원', '단체 급식 보조원', '분식 조리사', '사업체 구내식당 급식 조리사', '병원 급식 조리사',
                      '기타 음식서비스 종사원(병원 배식원)', '음료 조리사(바리스타 포함)', '주방 보조원(일반 음식점)']
        , '청소_및_기타_개인서비스직': ['기타 판매 단순 종사원(전단지배포, 벽보원, 물품 보관원)', '테마파크 서비스원', '재활용품 및 폐기물 수거원',
                             '호텔·콘도·숙박시설 청소원(룸메이드,하우스키퍼)', '주차 관리·안내원', '세탁원(다림질원)', '기타 서비스 단순종사원(사우나,찜질방 정리원 등)',
                             '매장 정리원(매장 보조원)', '도서 정리원', '환경 미화원', '세차원 및 운송장비 청소원', '주차 단속원 및 안전 순찰원', '외벽 및 창문 청소원']
        , '보건_의료직': ['병원행정 사무원(원무)', '안마사', '의료 보조원', '일반 간호사', '기타 보건·의료 서비스 종사원', '병원 코디네이터', '의무기록사']
        , '사회복지_종교직': ['직업상담사', '사회복지사(사회복지시설)', '재가 요양보호사', '그 외 사회복지 종사원']  # 장애인 생활지도원(장애인활동보조원 포함)
        , '돌봄_서비스직_간병_육아_': ['시설 요양보호사(노인요양사)', '장애인 생활지도원(장애인활동보조원 포함)']
        , '관리직_임원_부서장_': ['각종 단체 및 기타 고객서비스 관리자', '환경·청소 관리자', '기타 경영지원 서비스 관리자']
        , '경호_경비직': ['보안 관제원(경비 관제원)', '아파트·빌라 경비원', '건물 경비원(청사,학교,병원,상가,빌딩,공장 등)', '기타 건물 관리원(공원, 종교시설 등)']
        , '영업_판매직': ['기타 텔레마케터', '전기·전자장비 기술영업원', '요금 정산원(주차요금,통행료)', '매장 계산원', '편의점 판매원', '텔레마케터(콜센터)',
                     '콜센터 상담원(콜센터·고객센터·CS센터)', 'IT 기술영업원(전산장비,소프트웨어) ', 'IT 기술영업원(전산장비,소프트웨어)']  # IT 기술영업원(전산장비,소프트웨어)
        , '농림어업직': ['조경 식재원', '농업 단순 종사원', '식물 관리원', '농림어업 및 기타 생산 관리자', ]
        , '정보통신_연구개발직_및_공학기술직': ['정보시스템 운영자', '웹 운영자(홈페이지 관리자)', 'IT 테스터 및 IT QA 전문가', '웹 디자이너', '시스템 소프트웨어 개발자(프로그래머)',
                                 '웹 개발자(웹 엔지니어·웹 프로그래머)']
        , '스포츠_레크리에이션직': ['직업 운동선수']
        , '미용_예식_서비스직': ['네일 아티스트(손톱 관리사)']
        , '자연_생명과학_연구직': ['농어업 연구원 및 기술자']

    }

    emp_data['직종대분류'] = 0
    emp_data['직종중분류'] = 0

    for i in range(len(emp_data['모집직종'])):
        for name, lst in job_main_list.items():
            if emp_data['모집직종'].values[i] in lst:
                # print(f"리스트 '{name}'에서 값 {emp_data['모집직종'].values[i]}를 찾았습니다.")
                emp_data.loc[i, '직종대분류'] = name
                emp_data.loc[i, '직종중분류'] = emp_data['모집직종'].values[i]


    emp_data[['모집직종', '직종대분류', '직종중분류']]

    bool(job_s)

    if (bool(job_m) & bool(job_s)):
        emp_data = emp_data.loc[(emp_data['직종대분류'] == job_m) & (emp_data['직종중분류'] == job_s)]
    elif (job_m):
        emp_data = emp_data.loc[emp_data['직종대분류'] == job_m]

    extracted_data1 = pd.DataFrame()
    for name1 in emp_data['사업장명']:
        for name2 in barrier['시설물명']:
            if name1 in name2:
                extracted_data1 = pd.concat([extracted_data1, emp_data[emp_data['사업장명'] == name1]])
    extracted_data1 = extracted_data1.drop_duplicates(['연번'])
    extracted_data1

    extracted_data2 = pd.DataFrame()
    for name1 in emp_data['사업장명']:
        for name2 in safe['사업장명']:
            if name1 in name2:
                extracted_data2 = pd.concat([extracted_data2, emp_data[emp_data['사업장명'] == name1]])
    # extracted_data2 = extracted_data2.drop_duplicates(['연번'])

    barr_list = extracted_data1['사업장명'].tolist()
    barr_list = dict.fromkeys(barr_list)  # 리스트 값들을 key 로 변경
    barr_list = list(barr_list)

    safe_list = extracted_data2['사업장명'].tolist()
    safe_list = dict.fromkeys(safe_list)  # 리스트 값들을 key 로 변경
    safe_list = list(safe_list)

    emp_data['배리어프리'] = np.where(emp_data['사업장명'].isin(barr_list), '1', '0')
    emp_data['배리어프리'].value_counts()

    emp_data['안전사업장'] = np.where(emp_data['사업장명'].isin(safe_list), '1', '0')
    emp_data['안전사업장'].value_counts()

    # 선호조건 : 지역(경기도) + 대기업 + 연봉 + 안전(배리어 프리 여부)
    import pandas as pd

    max_weight = 0.6
    nomal_weight = 0.3
    min_weight = 0.1

    # n = input('지역')
    # p = input('대기업')
    # q = input('연봉')
    # r = input('안전')
    ### 분석

    emp_data['시급'] = np.where(emp_data['임금형태'] == '시급', emp_data['임금'], np.nan)
    emp_data['월급'] = np.where(emp_data['임금형태'] == '월급', emp_data['임금'], np.nan)
    emp_data['연봉'] = np.where(emp_data['임금형태'] == '연봉', emp_data['임금'], np.nan)

    emp_hour = emp_data.loc[emp_data['시급'].isnull() == False].drop(['월급', '연봉'], axis=1)
    emp_month = emp_data.loc[emp_data['월급'].isnull() == False].drop(['시급', '연봉'], axis=1)
    emp_year = emp_data.loc[emp_data['연봉'].isnull() == False].drop(['월급', '시급'], axis=1)

    # 시급
    emp_categori_hour = emp_hour.select_dtypes(include='object')
    emp_numeric_hour = emp_hour.select_dtypes(include='number')

    # 월급
    emp_categori_month = emp_month.select_dtypes(include='object')
    emp_numeric_month = emp_month.select_dtypes(include='number')

    # 연봉
    emp_categori_year = emp_year.select_dtypes(include='object')
    emp_numeric_year = emp_year.select_dtypes(include='number')

    # # 사업장 주소 지역(연)
    emp_categori_year['사업장_도'] = emp_categori_year['사업장 주소'].str.split(' ').str.get(0)
    emp_categori_year['사업장_시군구'] = emp_categori_year['사업장 주소'].str.split(' ').str.get(1)

    # # 사업장 주소 지역(월)
    emp_categori_month['사업장_도'] = emp_categori_month['사업장 주소'].str.split(' ').str.get(0)
    emp_categori_month['사업장_시군구'] = emp_categori_month['사업장 주소'].str.split(' ').str.get(1)

    # # 사업장 주소 지역(일)
    emp_categori_hour['사업장_도'] = emp_categori_hour['사업장 주소'].str.split(' ').str.get(0)
    emp_categori_hour['사업장_시군구'] = emp_categori_hour['사업장 주소'].str.split(' ').str.get(1)

    # if 근무지역이 선호조건이라면
    # # 우선 선택한 지역만 뽑
    # #

    # # from pandas.core.reshape.encoding import get_dummies
    cat_hour = emp_categori_hour
    cat_month = emp_categori_month
    cat_year = emp_categori_year

    # # 모집직종 먼저 필터링
    # # 모델링 결과 다시 보낼 떄 필요한 데이터 cat1
    cat_temp1_hour = cat_hour.loc[:,
                     ['사업장명', '요구경력', '요구학력', '구인신청일자', '모집기간', '모집직종', '임금형태', '고용형태', '등록일', '담당기관', '연락처', '사업장 주소',
                      '직종대분류', '직종중분류']]
    cat_temp1_month = cat_month.loc[:,
                      ['사업장명', '요구경력', '요구학력', '구인신청일자', '모집기간', '모집직종', '임금형태', '고용형태', '등록일', '담당기관', '연락처', '사업장 주소',
                       '직종대분류', '직종중분류']]
    cat_temp1_year = cat_year.loc[:,
                     ['사업장명', '요구경력', '요구학력', '구인신청일자', '모집기간', '모집직종', '임금형태', '고용형태', '등록일', '담당기관', '연락처', '사업장 주소',
                      '직종대분류', '직종중분류']]
    # '''
    # 사용자에게
    # '''

    # # 모델링에 필요한 데이터 -> cat_temp2
    cat_temp2_hour = cat_hour.loc[:, ['입사형태', '전공계열', '요구자격증', '기업형태', '사업장_도', '사업장_시군구', '배리어프리', '안전사업장']]
    cat_temp2_year = cat_year.loc[:, ['입사형태', '전공계열', '요구자격증', '기업형태', '사업장_도', '사업장_시군구', '배리어프리', '안전사업장']]
    cat_temp2_month = cat_month.loc[:, ['입사형태', '전공계열', '요구자격증', '기업형태', '사업장_도', '사업장_시군구', '배리어프리', '안전사업장']]
    # from pandas.core.reshape.encoding import get_dummies

    cat_temp2_hour['배리어프리'] = cat_temp2_hour['배리어프리'].astype('int')
    cat_temp2_year['배리어프리'] = cat_temp2_year['배리어프리'].astype('int')
    cat_temp2_month['배리어프리'] = cat_temp2_month['배리어프리'].astype('int')

    cat_temp2_hour['안전사업장'] = cat_temp2_hour['안전사업장'].astype('int')
    cat_temp2_year['안전사업장'] = cat_temp2_year['안전사업장'].astype('int')
    cat_temp2_month['안전사업장'] = cat_temp2_month['안전사업장'].astype('int')

    encoded_y = pd.DataFrame(pd.get_dummies(cat_temp2_year.iloc[:, :-2]))
    encoded_y.rename(columns = {'사업장_시군구_해운대구' : '사업장_시군구_해운대'}, inplace=True)
    encoded_m = pd.DataFrame(pd.get_dummies(cat_temp2_month.iloc[:, :-2]))
    encoded_m.rename(columns={'사업장_시군구_해운대구': '사업장_시군구_해운대'}, inplace=True)
    encoded_h = pd.DataFrame(pd.get_dummies(cat_temp2_hour.iloc[:, :-2]))
    encoded_h.rename(columns={'사업장_시군구_해운대구': '사업장_시군구_해운대'}, inplace=True)

    encoded_y = pd.concat([encoded_y, cat_temp2_year[['배리어프리', '안전사업장']]], axis=1)
    encoded_m = pd.concat([encoded_m, cat_temp2_month[['배리어프리', '안전사업장']]], axis=1)
    encoded_h = pd.concat([encoded_h, cat_temp2_hour[['배리어프리', '안전사업장']]], axis=1)
    # encoded_ori = encoded.copy()
    # #a.to_csv('test.txt',index=False,sep='\t')

    emp_numeric_hour.drop('임금', axis=1, inplace=True)
    emp_numeric_year.drop('임금', axis=1, inplace=True)
    emp_numeric_month.drop('임금', axis=1, inplace=True)

    # # 결과 추출후 사용자에게 알릴것 -> 고용형태, 임금형태
    # #기업에서 사용자에게 필수조건 : 입사형태가 경력일 경우-> 요구경력 보여주기, 요구학력
    # # 최종적으로 클라이언트에게 주는 리스트: 사업장명 리스트?

    from sklearn.preprocessing import MinMaxScaler
    sc1 = MinMaxScaler()
    sc2 = MinMaxScaler()
    sc3 = MinMaxScaler()
    emp_numeric_hour['급여점수'] = sc1.fit_transform(pd.DataFrame(emp_numeric_hour['시급'])) + 1
    emp_numeric_year['급여점수'] = sc2.fit_transform(pd.DataFrame(emp_numeric_year['연봉'])) + 1
    emp_numeric_month['급여점수'] = sc3.fit_transform(pd.DataFrame(emp_numeric_month['월급'])) + 1

    emp_numeric_month['급여점수'].unique()

    # 우선조건이 선택되었다면

    data1 = pd.DataFrame()
    data2 = pd.DataFrame()
    data3 = pd.DataFrame()
    '''
    입력값
    '''
    encoded_1 = pd.DataFrame()
    encoded_2 = pd.DataFrame()
    encoded_3 = pd.DataFrame()
    # 컬럼명 확인 및 인덱스 출력
    for j in important:
        for i in enumerate(encoded_y.columns):
            # if j not in i[1]:
            if j in i[1]:  # 정확한 값을 원하면 == 로 변경
                df1 = pd.DataFrame(encoded_y.loc[:, i[1]]) * 1.6  # 중요 가중치
                data1 = pd.concat([data1, df1], axis=1)
                print(i[1])
                encoded_1 = encoded_y.drop(str(i[1]), axis=1)
    encoded1 = encoded_1 * 1.3
    data1 = pd.concat([data1, encoded1], axis=1)
    data1 = pd.concat([pd.DataFrame(emp_numeric_year['급여점수']), data1], axis=1)

    for j in important:
        for i in enumerate(encoded_m.columns):
            # if j not in i[1]:
            if j in i[1]:  # 정확한 값을 원하면 == 로 변경
                df2 = pd.DataFrame(encoded_m.loc[:, i[1]]) * 1.6  # 중요 가중치
                data2 = pd.concat([data2, df2], axis=1)
                print(i[1])
                encoded_2 = encoded_m.drop(str(i[1]), axis=1)
    encoded2 = encoded_2 * 1.3
    data2 = pd.concat([data2, encoded2], axis=1)
    data2 = pd.concat([pd.DataFrame(emp_numeric_month['급여점수']), data2], axis=1)

    for j in important:
        for i in enumerate(encoded_h.columns):
            # if j not in i[1]:
            if j in i[1]:  # 정확한 값을 원하면 == 로 변경
                df3 = pd.DataFrame(encoded_h.loc[:, i[1]]) * 1.6  # 중요 가중치
                data3 = pd.concat([data3, df3], axis=1)
                print(i[1])
                encoded_3 = encoded_h.drop(str(i[1]), axis=1)
    encoded3 = encoded_3 * 1.3
    data3 = pd.concat([data3, encoded3], axis=1)
    data3 = pd.concat([pd.DataFrame(emp_numeric_hour['급여점수']), data3], axis=1)

    # data# 경력 컬럼 주의

    data3

    data1['총합'] = data1.sum(axis=1)
    data2['총합'] = data2.sum(axis=1)
    data3['총합'] = data3.sum(axis=1)
    print(data1)

    temp1 = pd.concat([cat_temp1_year, data1, emp_numeric_year['연번']], axis=1)
    #
    temp2 = pd.concat([cat_temp1_month, data2, emp_numeric_month['연번']], axis=1)
    # temp2 = temp2.loc[temp2['모집직종'].str.contains('사무')]
    temp3 = pd.concat([cat_temp1_hour, data3, emp_numeric_hour['연번']], axis=1)
    # temp3 = temp3.loc[temp3['모집직종'].str.contains('사무')]
    rec1 = temp1.sort_values(by='총합', ascending=False).head(5)
    rec2 = temp2.sort_values(by='총합', ascending=False).head(5)
    rec3 = temp3.sort_values(by='총합', ascending=False).head(5)

    print(data1)

    n = 4  # 출력할 상위 n개의 비중을 가지는 컬럼과 값
    print(temp1)
    reason1 = rec1.iloc[:, 14:-2]
    # 행별 상위 n개의 비중을 가지는 컬럼과 해당 값 출력
    top_columns = reason1.apply(lambda row: row[row > 1.3].nlargest(n).index.tolist(), axis=1)
    #top_values = reason1.apply(lambda row: row[row > 1.3].nlargest(n).values.tolist(), axis=1)
    rec1['추천이유'] = top_columns
    # for i in range(len(rec1['급여점수'])):
    #     if rec1['급여점수'].iloc[i] > 1.3:
    #         rec1['추천이유'].iloc[i].append('임금')

    reason2 = rec2.iloc[:, 14:-2]
    top_columns = reason2.apply(lambda row: row[row > 1.3].nlargest(n).index.tolist(), axis=1)
    rec2['추천이유'] = top_columns
    # for i in range(len(rec2['급여점수'])):
    #     if rec2['급여점수'].iloc[i] > 1.3:
    #         rec2['추천이유'].iloc[i].append('임금')

    reason3 = rec3.iloc[:, 14:-2]
    top_columns = reason3.apply(lambda row: row[row > 1.3].nlargest(n).index.tolist(), axis=1)
    # np.where(rec3['배리어프리'] == 1.3,
    # top_columns.append()
    rec3['추천이유'] = top_columns
    # for i in range(len(rec3['급여점수'])):
    #     if rec3['급여점수'].iloc[i] > 1.3:
    #         rec3['추천이유'].iloc[i].append('임금')

    print(data1)

    # emp_temp = emp_data.iloc[condition]#.loc[emp_data['모집직종1'] == '사무원']
    res = pd.DataFrame()
    hap = pd.DataFrame()
    reason = pd.DataFrame()
    hap['총합'] = pd.concat([rec1['총합'], rec2['총합'], rec3['총합']])
    reason['추천이유'] = pd.concat([rec1['추천이유'], rec2['추천이유'], rec3['추천이유']])
    res = pd.concat([emp_data.loc[rec1.index], emp_data.loc[rec2.index], emp_data.loc[rec3.index]]).drop(
        ['시급', '월급', '연봉'], axis=1)
    res = pd.concat([res, hap, reason], axis=1)
    res = res.sort_values(by='총합', ascending=False)
    res['배리어프리'] = res['배리어프리'].astype(int)
    res['안전사업장'] = res['안전사업장'].astype(int)

    for i in range(len(res['배리어프리'])):
        if res['배리어프리'].iloc[i] == 1:
            res['추천이유'].iloc[i].append('배리어프리인증')
    print(res)

    for i in range(len(res['안전사업장'])):
        if res['안전사업장'].iloc[i] == 1:
            res['추천이유'].iloc[i].append('안전사업장')
    res

    
    #sc4 = MinMaxScaler()

    #res['총합'] = sc4.fit_transform(pd.DataFrame(res['총합'])) * 100
    #res['총합'].apply(np.ceil).astype(int)  # 30 점 아래
    #res['총합'] = np.where(res['총합'] == 0, 10, res['총합'])
    res = res.to_json(orient='records',force_ascii=False,indent = 4)

    return res
