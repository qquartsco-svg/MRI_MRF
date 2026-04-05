# examples

> **한국어 (정본).** English: [README_EN.md](README_EN.md)

## full_scenario.py

저장소 루트에서 실행:

```bash
python3 examples/full_scenario.py
```

`analyze()`에 Larmor, 자기 가두기, 열 proxy, 지구–L1–달 게이트 토폴로지, 플라즈마 수송, 토로이달 형상, RF 링크, 라그랑주 L1을 한 번에 넣어 **통합 Ω·ATHENA·verdict**를 출력합니다.

## factory_handoff_demo.py

저장소 루트에서 실행:

```bash
python3 examples/factory_handoff_demo.py
```

이 예제는 MRF 결과가 실제로 Factory 계열로 어떻게 내려가는지 보여줍니다.

- `MRI PATH -> MTF`
- `Gate PATH -> MTF`
- `Gate PATH -> Foundry`
- `Gate PATH -> fabless-style semiconductor chain`

개념 배경은 상위 디렉터리 [CONCEPT.md](../CONCEPT.md)를 참고하세요.
