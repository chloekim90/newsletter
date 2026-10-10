# 오늘의 4분 뉴스

평일 아침 뉴스 브리프 아카이브.

- 새 호 올리기: `python3 publish.py --date YYYY-MM-DD --src <뉴스레터.html> --title "<헤드라인>" --summary "<한 줄>"` 후 commit·push
- 광고 코드: `partials/head.html`(공통 스크립트), `partials/ad-top.html`, `partials/ad-bottom.html`에 넣고 `python3 publish.py --rebuild`
- 주소가 바뀌면 `site.json` 수정 후 `--rebuild`
