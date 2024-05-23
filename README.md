# 👩‍💻 ONELAB AI 프로젝트

### AI 프로젝트 소개
- 맡은 기능
  
  > 게시글 상세페이지 내부에서 첨부되어있는 파일과 유사한 파일이 있는 상위 4개의 게시글을 추천해주는 시스템입니다.

### 목차
1. 화면 소개
2. 데이터 수집 (Data Crowling - BeautifulSoup)
3. 유사도 분석 (Cosine similarity)
4. Django 적용

---

### 1. 화면 소개
- 자료 공유 서비스 특성 상, 게시글 상세페이지에는 파일이 첨부되어 있습니다.
- 해당 파일의 글을 읽어온 뒤, 유사한 게시글을 추천해주는 시스템을 구현했습니다.
<details>
  <summary>적용할 화면 확인하기</summary>
  <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/5bb872f1-c521-4447-b623-568af0c00be6">
</details>

### 2. 데이터 수집 및 유사도 분석
- 수집해야할 데이터

  > 내용(텍스트) 분석이 주 이기 때문에, 내용이 많은 네이버 뉴스를 활용하기로 결정하였습니다.
- BeautifulSoup를 활용하여 데이터를 수집, python에서 데이터를 csv파일로 내보냈습니다. jupyter notebook환경에서 fit을 진행하였습니다.
- 유사도 분석이 잘 되는 것을 확인하고 이후에 Django 서버에 적용했습니다.
<details>
  <summary>크롤링 과정 확인하기</summary>
  <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/9f2f8748-59bf-45a7-99c5-8d68f1c205ce" width="500px;">
</details>

### 3. 유사도 분석 (Cosine similarity)
1. python에서 크롤링한 데이터 csv 파일을 jupyter notebook에서 불러와서 확인하였습니다.
       
   <details>
       <summary>코드 확인</summary>
       <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/b3de9296-f874-4830-8598-1087c69e169e" width="600px;"> 
  </details>

2. 내용만을 가져온 뒤, 벡터화를 위해 sklearn 라이브러리의 CountVectorizer에 fit_transform을 진행하였습니다.
3. 벡더화된 결과를 sklearn 라이브러리의 cosine_similarity에 넣어 유사도를 나타냈습니다.

   <details>
     <summary>코드 확인</summary>
     <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/835ced06-f663-425c-85e3-bbd810236ed7" width="600px;">
   <details>

 4. 상위 5개의 유사도를 나타내기 위해 리스트의 argsort 메소드를 이용해 나타냈습니다.

    <details>
      <summary>코드 확인</summary>
      <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/9d990081-b813-4374-be62-95ab0c5d5b0e" width="600px;"> 
    </details>

5. 일련의 과정을 반복하며 대략 1000개의 데이터를 수집하였고, conact을 이용해 하나의 데이터 세트로 합쳐서 csv 파일로 내보내는 것으로 데이터 수집을 마쳤습니다.

### 4. Django 적용 과정
1. 자료 공유 서비스에는 'pdf, hwp, docx, xlsx' 총 4개의 확장자의 파일이 들어갈 수 있습니다. 이에 확장자에 따라서 파일의 텍스트를 가져오는 것을 우선적으로 진행하였습니다.
  - 업로드 되는 파일이 각각 다른 확장자를 지니고 있으며, 확장자 마다 텍스트를 읽어오는 방식이 다르기 때문에 각 확장자 별 함수를 선언하였습니다.  
  - hwp, docx, xlsx은 pandas 라이브러리 내의 함수를 이용해 텍스트를 가져왔습니다.
    <br>
    <details>
      <summary>엑셀 및 워드 파일의 텍스트 읽어오는 과정</summary>
      
      [엑셀]  
      
      <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/b84a98b0-914d-438f-8325-3d909edd90f9" width="600px">  
      
      [워드]  
      
      <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/a5dda79d-6d50-4d7f-a00c-670db7995c28" width="600px">
    </details>
    
  - pdf 파일의 경우, PyMuPDF라이브러리를 이용하여 파일의 첫 번째 페이지를 이미지(png)로 변환하고 OCR(네이버 클로바)을 이용하여 해당 이미지의 텍스트를 읽어왔습니다.
    <br>
      <details>
        <summary>PDF를 이미지로 변환하는 과정 (PyMuPDF 라이브러리 이용)</summary>
        <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/e69faeef-e285-4a9e-a3fe-dd639507eb2f" width="600px;">
      </details>
      
      <details>
        <summary>이미지를 텍스트로 읽어오는 과정 (OCR-Naver Clova 이용)</summary>
        <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/cc41a42a-4340-41ae-be38-d0e7bcab2cd0" width="600px;">
      </details>

2. 읽어온 텍스트들은 ShareFileContent라는 유사도 테이블에 Insert되게 구현하였습니다. 즉, 사용자가 게시글을 작성하면 자동으로 파일의 텍스트만 추출됩니다.
   <details>
      <summary>텍스트만 추출되어 유사도 테이블에 저장되는 과정</summary>
      <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/c01e5a0d-425d-4177-853f-812a28de25a1" width="600px;">
    </details>

3. 상세 페이지로 이동할 때, 유사도 테이블 전체를 불러와서 현재 게시물 내의 파일과의 유사도 분석을 진행합니다.
   <details>
     <summary>유사도 분석 과정</summary>  
     
     [3-1. 상세 페이지 로드 시, 유사도 분석 함수 호출]
   
     <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/a0be18fc-0ab6-42f0-aeec-9fcb489a50bf" width="600px">  

     [3-2. 현재 파일을 기준으로 다른 파일들과 유사도 분석 진행]
   
     <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/d19f9437-19ab-45f1-86cc-85c043f2f3ed" width="600px">
     <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/9438b1ea-8e27-4229-83d1-06a2498cc26d" width="600px">
   </details>

4. 유사도 분석이 완료 된 후, 유사한 게시물 상위 4개가 리스트 형태로 리턴되면 해당 게시글들이 화면에 보여지게됩니다.
   <details>
      <summary>유사도 분석이 완료된 화면 확인하기</summary>
      <img src="https://github.com/SOYOUNGdev/project_onelab_AI/assets/115638411/cece947d-5926-4d1d-8b27-13f847681187" width="600px;">
  </details>

### 5. 서버 배포 및 화면 시연
- 개인 로컬에서 작업한 AI 서비스가 잘 작동되는 것을 확인하고 ubuntu와 aws를 이용하여 서버에 배포하였습니다.
     
### 6. Trouble Shooting
- 




