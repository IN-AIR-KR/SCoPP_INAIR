# SCoPP 논문 실내 재현 및 Multi-robot Indoor Coverage Path Planning 구현 
(https://github.com/onelkhjh/Multi-robot_Indoor_Coverage_Path-Planning)

## Clustering baseline

- `official_minibatch` is the default and the official SCoPP clustering
  baseline. Official comparison and KPI artifacts must use this profile.
- `deterministic_lloyd` is a non-default legacy/test profile retained for
  historical reproduction and deterministic unit tests. It must not be used
  for official comparison or KPI artifacts.
- Comparisons must keep the map, clustering/allocation, and constraints fixed.
  See [the official parity audit](docs/official_parity_audit.md) for details.

## 클러스터링 기준선

- `official_minibatch`를 기본값이자 공식 SCoPP 클러스터링 기준선으로 사용한다.
  공식 비교 및 KPI 산출물은 반드시 이 프로파일을 사용한다.
- `deterministic_lloyd`는 과거 결과 재현과 결정론적 단위 테스트를 위한 비기본
  레거시/테스트 프로파일로만 유지한다. 공식 비교 및 KPI 산출물에는 사용하지 않는다.
- 비교할 때는 맵, 클러스터링/할당, 제약 조건을 동일하게 고정한다. 자세한 내용은
  [공식 코드 정합성 문서](docs/official_parity_audit.ko.md)를 참고한다.

## 한국어

이 저장소는 Leighton Collins et al.의 논문 *Scalable Coverage Path Planning of Multi-Robot Teams for Monitoring Non-Convex Areas* (arXiv:2103.14709)과 저자 공식 코드를 기준선으로 두고, 같은 조건에서 더 나은 KPI를 만드는 방향으로 진행한다.

기준선으로 유지하는 범위는 clustering, auction, coverage path planning이다. 이 세 단계는 논문 재현의 기준으로 남겨두되, 실제 작업 초점은 실내 비행에 더 적합한 경로와 지표를 만드는 쪽에 둔다.

이 프로젝트는 Multi-robot Indoor Coverage Path Planning으로 정리한다. 따라서 direct-distance와 executable-distance를 섞지 않고, 동일한 맵과 동일한 할당, 동일한 제약 조건에서만 비교한다.

## 핵심 방향

- baseline reference: SCoPP 논문 + 공식 코드
- comparison focus: 같은 상태에서의 KPI 비교
- optimization focus: 실내 비행에 더 적합한 경로와 지표
- reporting discipline: direct-distance와 executable-distance를 섞지 않음
- reference retention: clustering, auction, coverage path planning은 기준선으로 유지

## 현재 보관 중인 핵심 결과물

- `artifacts/path_planner_exec_only_v1.json`
- `artifacts/path_planner_exec_only_v1.png`
- `artifacts/executable_kpi_result.md`
- `artifacts/indoor_lab.png`
- `artifacts/indoor_lab_plan.png`
- `artifacts/indoor_lab_metrics.json`
- `artifacts/paper_like.png`

## 생성 방법

UI는 Python 스크립트가 생성하고, 원본 템플릿은 `src/scopp/ui/`에 둔다.

```powershell
python -m pip install -e ".[test]"
python -m pytest
python scripts/build_path_ui.py examples/maps/indoor_lab.yaml --output artifacts/path_ui.html
python scripts/build_progress_ui.py --output artifacts/progress_ui.html
python scripts/build_path_comparison_ui.py examples/maps/indoor_lab.yaml --output artifacts/path_comparison_ui.html --seed 0 --bias 0.5
python scripts/compare_path_planners.py examples/maps/indoor_lab.yaml --seed 0 --bias 0.5 --output artifacts/path_planner_exec_only_v1.json --plot artifacts/path_planner_exec_only_v1.png
```

## 실행 기준 비교 결과

핵심 비교 결과는 `artifacts/path_planner_exec_only_v1.png` 이다. 이 결과는 동일한 `grid-adjacent executable` 모델과 no-fly 차단 조건에서 Metric-TSP와 public-code NN을 비교한다.

요약 문서는 `artifacts/executable_kpi_result.md` 에 있다.


## 참고

- `path_ui.html`, `progress_ui.html`, `path_comparison_ui.html` 는 Python 스크립트가 생성하는 UI 템플릿이다.
- 최종 KPI 보고는 direct-distance 숫자를 사용하지 않는다.

---

## Attribution and third-party software

MICPP_INAIR is an independently structured derivative implementation informed by the SCoPP paper and the authors' MIT-licensed official implementation. It is not a byte-for-byte copy or an official release of the SCoPP authors.

- Upstream reference: [adamslab-ub/SCoPP](https://github.com/adamslab-ub/SCoPP)
- Paper: Collins et al., *Scalable Coverage Path Planning of Multi-Robot Teams for Monitoring Non-Convex Areas*, ICRA 2021, arXiv:2103.14709
- Retained reference behavior: clustering, conflict-cell auction, and coverage-path planning baseline
- Project adaptations: indoor Cartesian maps, boundary policies, no-fly handling, executable transit, KPI reporting, and experiment UIs

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for dependency and attribution details. No license is granted for this repository's original work merely by this notice; a repository-level license must be selected separately by its owner.
