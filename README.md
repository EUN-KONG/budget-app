# 나만의 용돈 기입장

Python 표준 라이브러리만 사용한 파일 기반 콘솔 가계부입니다.

거래 CRUD, 검색, 월별 요약, 예산 및 카테고리 관리, CSV 가져오기와 내보내기를 지원합니다.

## 실행 환경

- Python 3.10 이상
- 외부 라이브러리 설치 불필요

Python 버전 확인:

```bash
python3.12 --version
```

전체 도움말:

```bash
python3.12 -m budget_app --help
```

## 데이터 저장

기본 데이터 폴더는 프로젝트 최상위의 `data/`입니다.

- `data/transactions.jsonl`: 거래 내역
- `data/categories.jsonl`: 카테고리
- `data/budgets.jsonl`: 월별 예산

모든 데이터는 UTF-8 JSONL 형식으로 영구 저장됩니다. JSONL은 JSON 데이터 한 건을 한 줄에 저장하는 형식입니다.

저장 폴더를 변경하려면 `--data-dir`을 명령어보다 앞에 입력합니다.

```bash
python3.12 -m budget_app --data-dir ./my_data list
```

처음 실행하면 저장 파일이 자동으로 생성됩니다. 카테고리 파일이 비어 있으면 다음 기본 카테고리가 생성됩니다.

- `food`
- `transport`
- `rent`
- `salary`
- `etc`

## 주요 명령

### 거래 추가

대화형으로 거래 정보를 입력합니다.

```bash
python3.12 -m budget_app add
```

거래 타입은 `income` 또는 `expense`만 사용할 수 있으며 금액은 양수 정수여야 합니다.

### 거래 목록

최신 거래 10건을 출력합니다.

```bash
python3.12 -m budget_app list
```

출력 개수 지정:

```bash
python3.12 -m budget_app list --limit 5
```

### 거래 검색

```bash
python3.12 -m budget_app search --type expense
python3.12 -m budget_app search --category food
python3.12 -m budget_app search --from 2026-01-01 --to 2026-12-31
python3.12 -m budget_app search --q 점심
python3.12 -m budget_app search --tag meal
```

검색 조건을 여러 개 함께 사용할 수도 있습니다.

### 거래 수정

수정 방식은 대화형으로 고정합니다. 엔터를 누르면 기존 값을 유지하고, 메모나 태그에 `-`를 입력하면 기존 값을 삭제합니다.

```bash
python3.12 -m budget_app update --id TX-000001
```

### 거래 삭제

```bash
python3.12 -m budget_app delete --id TX-000001
```

없는 ID를 입력하면 오류 메시지와 종료 코드 `1`을 반환합니다.

### 카테고리 관리

```bash
python3.12 -m budget_app category list
python3.12 -m budget_app category add
python3.12 -m budget_app category remove
```

거래에서 사용 중인 카테고리는 삭제할 수 없습니다.

### 월별 예산 설정

```bash
python3.12 -m budget_app budget set --month 2026-09 --amount 500000
```

### 월별 요약

```bash
python3.12 -m budget_app summary --month 2026-09 --top 3
```

다음 내용을 출력합니다.

- 총수입
- 총지출
- 잔액
- 카테고리별 지출 TOP N
- 예산 사용률
- 예산 초과 경고

## CSV 가져오기

```bash
python3.12 -m budget_app import --from import.csv
```

등록되지 않은 카테고리나 잘못된 날짜, 타입, 금액이 있으면 행 번호와 오류 원인을 출력합니다.

## CSV 내보내기

월 조건:

```bash
python3.12 -m budget_app export --out export.csv --month 2026-09
```

기간 조건:

```bash
python3.12 -m budget_app export --out export.csv --from 2026-09-01 --to 2026-09-30
```

내보내기에는 `--month`, `--from`, `--to` 중 하나 이상의 날짜 조건이 필요합니다.

## CSV 스키마

CSV 파일은 UTF-8, 헤더 포함 형식이어야 합니다.

| column | 필수 값 | 설명 |
| --- | --- | --- |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` 또는 `expense` |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | 양수 정수 |
| `memo` | N | 문자열 |
| `tags` | N | 쉼표로 구분한 문자열 |

예시:

```csv
date,type,category,amount,memo,tags
2026-09-25,expense,food,12000,점심,"meal,work"
```

태그가 여러 개라면 CSV 규칙에 따라 큰따옴표로 감쌉니다.

## 프로그램 구조

```text
budget_app/
├── __init__.py
├── __main__.py
├── cli.py
├── decorators.py
├── models.py
├── repositories.py
├── services.py
└── storage.py
```

- `models.py`: 거래 데이터 구조
- `repositories.py`: JSONL 파일 읽기와 쓰기
- `services.py`: 검증, 검색, 요약, CSV 처리
- `cli.py`: 명령어와 사용자 입출력
- `decorators.py`: 공통 예외 처리
- `storage.py`: 데이터 폴더와 파일 초기화

거래 목록과 검색은 제너레이터를 이용해 파일을 한 건씩 처리합니다.

## 종료 코드

- 정상 종료: `0`
- 오류 종료: `1`
- 잘못된 명령어나 필수 옵션 누락: `2`

오류 발생 시 스택트레이스 대신 오류 원인과 해결 힌트를 출력합니다.