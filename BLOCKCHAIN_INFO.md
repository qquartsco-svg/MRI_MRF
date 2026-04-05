# 블록체인/서명 안내

이 저장소는 온체인 스마트컨트랙트를 포함하지 않습니다.

대신 `SIGNATURE.sha256` 파일로 릴리스 스냅샷을 고정합니다.

- 생성: `python3 scripts/generate_signature.py`
- 검증: `python3 scripts/verify_signature.py`
- 패키지 정체성 점검: `python3 scripts/verify_package_identity.py`
- 통합 릴리스 체크: `python3 scripts/release_check.py`

의미:
- 서명 시점의 파일 집합과 현재 파일 집합이 같은지 확인
- 문서/코드/테스트가 함께 움직였는지 점검
- 공개 정본 위생 유지
