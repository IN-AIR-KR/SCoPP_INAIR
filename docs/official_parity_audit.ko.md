# 공식 SCoPP 코드 정합성 검증

## 검증 자료

- Collins et al., *Scalable Coverage Path Planning of Multi-Robot Teams for
  Monitoring Non-Convex Areas*, arXiv:2103.14709
- `adamslab-ub/SCoPP` 공식 공개 저장소의 `monitoring_algorithms.py` 및
  `SCoPP_settings.py` (`main` 브랜치, 2026-07-05 확인)

## 공식 구현에서 확인된 동작

| 단계 | 공식 구현 동작 |
|---|---|
| Cell 폭 | `W = 2h tan(F/2)`를 계산한 뒤 정수로 변환하고 홀수이면 1을 빼서 짝수로 만든다. |
| Cell 포함 | cell 둘레를 3 m 간격으로 표본화하고 필요한 둘레점이 AOI 내부에 모두 존재할 때 포함한다. |
| 영역 분할 | cluster 수는 노드 수이며 `MiniBatchKMeans`, 허용오차 `cell_size/8`, 최대 10회를 사용한다. |
| Cluster와 노드 연결 | 각 cluster에서 가장 가까운 cell을 기준으로 아직 연결되지 않은 로봇 시작점을 탐욕적으로 연결한다. |
| Conflict 판정 | 한 cell의 표본화된 둘레에 둘 이상의 cluster label이 있으면 conflict cell이다. |
| Conflict 입찰 | 경매 전에 `distance_bias = round(d0/cell_size) × B`를 고정하고 `현재 cell 수 + distance_bias`를 최소화한다. 기본 `B=0.5`다. |
| 경로 계획 | 할당 cell 중심에 대해 Euclidean nearest-neighbor를 반복한다. 공식 기본 `nn` 분기는 brute-force 탐색을 사용한다. |
| 경로 종료 | 각 경로는 로봇 시작점에서 출발해 마지막에 시작점으로 복귀한다. |

## 현재 구현에 반영한 수정

- conflict 거리 bias를 cell 폭 단위로 정규화하고 반올림한다.
- 경매가 시작된 뒤에는 거리 bias를 다시 계산하지 않는다.
- nearest-neighbor 경로가 마지막에 시작점으로 복귀하도록 수정했다.
- 동일 입찰 비용에서는 기존 후보 순서를 유지한다.

## 실내 실험을 위한 의도적 변경

- 위도·경도 대신 미터 단위 로컬 Cartesian 좌표를 사용한다.
- 공식 코드의 정수·짝수 cell 폭 변환을 적용하지 않는다. 현재 실험의 약 `0.924 m`
  cell은 공식 규칙을 적용하면 0이 되므로 사용할 수 없다.
- 전체 AOI를 빠뜨리지 않기 위한 `any_overlap` 정책을 제공한다.
- perimeter 표본 간격은 3 m가 아니라 `W/8`을 기본값으로 사용한다.
- 논문 설명에 맞춰 자체 2차원 KD-tree로 nearest-neighbor를 계산한다.
- 실제 격자 이동은 AOI/no-fly 제약을 지키는 4-neighbor A* transit 경로로 전개한다.
  이는 논문의 방문 순서 이후에 추가한 실내 실행 제약이다.

## 구현된 공식 clustering profile

`official_minibatch` profile을 추가했다. 이 profile은 공식 코드의
`MiniBatchKMeans`, 최대 10회, `W/8` tolerance와 greedy cluster-to-node 연결을
사용한다. 재현 가능한 실험을 위해 random seed를 명시적으로 기록한다. 기존 방식은
`deterministic_lloyd`는 비기본 레거시/테스트 profile로만 유지하며 공식 비교 및
KPI 산출물에는 사용하지 않는다.

다만 현재 scikit-learn 1.9에서 과거 공식 코드 당시의 라이브러리 내부 동작까지 완전히
재현한다고 보장할 수는 없다. `batch_size=100`, `n_init=3`으로 과거 기본값을 명시했으며,
직접 비교 시에는 profile, seed 및 라이브러리 버전을 함께 보고해야 한다.
