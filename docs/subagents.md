# 서브 에이전트 역할 정의

이 문서는 프로젝트에서 쓰는 서브 에이전트 역할을 정리한다. 역할은 baseline reference와 개선 실험을 섞지 않기 위해 분리한다.

## 역할

- `paper-verifier`
  - 논문과 공식 자료를 기준으로 baseline 해석을 검증한다.
  - 코드는 수정하지 않고 요구사항, 불확실성, traceability를 정리한다.
- `map-engineer`
  - 맵 모델, 격자화, 시각화를 담당한다.
  - 좌표계, 단위, cell 정책을 명시적으로 유지한다.
- `algorithm-engineer`
  - clustering, conflict auction, path planning을 구현한다.
  - baseline reference와 개선 실험을 분리한다.
- `reproduction-tester`
  - 독립적으로 테스트와 재현 실험을 확인한다.
  - KPI 차이, 오차, 재현성 문제를 보고한다.
- `review-supervisor`
  - 근거, 구현, 테스트가 서로 맞는지 검토한다.
  - 성급한 완료 판정을 막는다.

## 사용 원칙

1. 역할은 bounded task에만 쓴다.
2. baseline reference와 개선 실험을 같은 산출물에 섞지 않는다.
3. 역할 정의는 이 문서를 기준으로 하며, README와 AGENTS는 이 문서를 참조한다.
