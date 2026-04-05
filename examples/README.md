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

## space_gate_datacenter_demo.py

저장소 루트에서 실행:

```bash
python3 examples/space_gate_datacenter_demo.py
```

이 예제는 우주 게이트 자체를 내부 대기 순환형 데이터센터로 보고,

- 내부 공냉/대류
- 자기공명 보조 열수송
- 외부 라디에이터 복사

를 **서로 섞지 않고 층별로** 스크리닝하는 데모입니다.

## system_stack_demo.py

저장소 루트에서 실행:

```bash
python3 examples/system_stack_demo.py
```

이 예제는 MRF를 상위 시스템 관점에서 한 번에 보여줍니다.

- `MRF -> SpaceThermal`
- `MRF -> Satellite`
- `MRF -> Orbital`
- `MRF -> Manufacturing`
- `MRF -> Foundry`
- `MRF -> Fabless`
- `MRF -> Superconducting_Magnet_Stack`

개념 배경은 상위 디렉터리 [CONCEPT.md](../CONCEPT.md)를 참고하세요.
