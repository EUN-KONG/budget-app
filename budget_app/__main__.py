# python3.12 -m budget_app 명령을 실행하면 cli.py의 main 함수가 시작됩니다.
from budget_app.cli import main

# main 함수가 반환한 숫자를 프로그램의 종료 코드로 사용합니다.
raise SystemExit(main())
