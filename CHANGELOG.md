# CHANGELOG


## v0.6.1 (2026-03-17)

### Bug Fixes

- Refactor dropdown click handling to use document-level event delegation (#32)
  ([#32](https://github.com/platzhersh/oehrpy/pull/32),
  [`c1b8f1f`](https://github.com/platzhersh/oehrpy/commit/c1b8f1fc7a58ae7d59897465b40dcce86ee47a3d))


## v0.6.0 (2026-03-13)

### Code Style

- Refactor layout from CSS Grid to Flexbox with improved responsiveness (#30)
  ([#30](https://github.com/platzhersh/oehrpy/pull/30),
  [`f1007c9`](https://github.com/platzhersh/oehrpy/commit/f1007c9b20615b08ec5771faf4e4b167daecc495))

### Features

- Add web GUI tools: converter, explorer, and migration helper (#31)
  ([#31](https://github.com/platzhersh/oehrpy/pull/31),
  [`d169919`](https://github.com/platzhersh/oehrpy/commit/d169919d797168b437a5c1049b4f28de4ddfc3ef))


## v0.5.0 (2026-03-12)

### Code Style

- Align validator page styling with docs site branding (#27)
  ([#27](https://github.com/platzhersh/oehrpy/pull/27),
  [`f00f051`](https://github.com/platzhersh/oehrpy/commit/f00f0515352f05521bc964a9b809952a014cb3f9))

### Features

- Add OPT validator with XML, semantic, structural, and FLAT path checks (#29)
  ([#29](https://github.com/platzhersh/oehrpy/pull/29),
  [`e853d39`](https://github.com/platzhersh/oehrpy/commit/e853d39a75730b36abb95b312173865dab34ae8b))


## v0.4.0 (2026-03-12)

### Features

- Add Pyodide integration for Python-backed FLAT validator (#26)
  ([#26](https://github.com/platzhersh/oehrpy/pull/26),
  [`5637e2f`](https://github.com/platzhersh/oehrpy/commit/5637e2fa6c3ad645798915af615122b5655b08e7))


## v0.3.0 (2026-03-12)

### Features

- Add FLAT format validator with web UI and Python API (#24)
  ([#24](https://github.com/platzhersh/oehrpy/pull/24),
  [`6e18d76`](https://github.com/platzhersh/oehrpy/commit/6e18d7647c11f6c4cecd81a3c5b08017c9062d56))


## v0.2.1 (2026-02-04)

### Bug Fixes

- Support EHRBase 2.0 JSON format and improve composition retrieval (#21)
  ([#21](https://github.com/platzhersh/oehrpy/pull/21),
  [`9afd769`](https://github.com/platzhersh/oehrpy/commit/9afd769c073cc2dea5c084d279fd42a6c02fb691))


## v0.2.0 (2026-02-04)

### Documentation

- Add PRDs for composition lifecycle, audit, builders, and EHR management (#19)
  ([#19](https://github.com/platzhersh/oehrpy/pull/19),
  [`1542994`](https://github.com/platzhersh/oehrpy/commit/1542994dd9c5319b268041ab6f114d45377a3791))

### Features

- Add composition versioning and update operations (PRD-0002) (#20)
  ([#20](https://github.com/platzhersh/oehrpy/pull/20),
  [`eadb0c9`](https://github.com/platzhersh/oehrpy/commit/eadb0c9f7714aa4bbfb0e7fce3cbd8e6481a7ce9))


## v0.1.1 (2026-01-31)

### Bug Fixes

- Resolve integration test failures against EHRBase 2.0 (#18)
  ([#18](https://github.com/platzhersh/oehrpy/pull/18),
  [`ca63003`](https://github.com/platzhersh/oehrpy/commit/ca6300326200e5a497f895c6a6f0ce67d4fecffc))


## v0.1.0 (2026-01-31)

### Bug Fixes

- Install build module inside semantic-release Docker container (#17)
  ([#17](https://github.com/platzhersh/oehrpy/pull/17),
  [`23ced62`](https://github.com/platzhersh/oehrpy/commit/23ced6206b6f18ad8e55576c3201b0afdb60685a))

- Update FLAT format paths based on EHRBase 2.26.0 web template (#11)
  ([#11](https://github.com/platzhersh/oehrpy/pull/11),
  [`1a4d0aa`](https://github.com/platzhersh/oehrpy/commit/1a4d0aaca0640711ceef771e00ba5e16560ee523))

### Documentation

- Add contribution guidelines (#14) ([#14](https://github.com/platzhersh/oehrpy/pull/14),
  [`8b12373`](https://github.com/platzhersh/oehrpy/commit/8b123738235b96e226e356ff9a0484a056f639c8))

- Add OPT Parser documentation to GitHub Pages (#9)
  ([#9](https://github.com/platzhersh/oehrpy/pull/9),
  [`7ed27de`](https://github.com/platzhersh/oehrpy/commit/7ed27de53baaddc53c50e23cc4d4613495f339bf))

### Features

- Add automated release workflow with python-semantic-release (#16)
  ([#16](https://github.com/platzhersh/oehrpy/pull/16),
  [`8201f6a`](https://github.com/platzhersh/oehrpy/commit/8201f6aadc9b7e008bcaf5d4a12c0880222852e1))

- Add complete OPT (Operational Template) support with builder generation (#8)
  ([#8](https://github.com/platzhersh/oehrpy/pull/8),
  [`f938e23`](https://github.com/platzhersh/oehrpy/commit/f938e23293db86c613b041e8301403367325b82c))

- Add GitHub Actions CI/CD workflow (#3) ([#3](https://github.com/platzhersh/oehrpy/pull/3),
  [`ad43fdd`](https://github.com/platzhersh/oehrpy/commit/ad43fdd104dea399efdc013f718ee94f9df01ad5))

- Add PyPI publishing support (#13) ([#13](https://github.com/platzhersh/oehrpy/pull/13),
  [`052e447`](https://github.com/platzhersh/oehrpy/commit/052e44759657f036114e7eab8a652b0cb0883aae))

- Implement features from PRD-0000 (#2) ([#2](https://github.com/platzhersh/oehrpy/pull/2),
  [`829ea0b`](https://github.com/platzhersh/oehrpy/commit/829ea0bde75e20d1b72c4c2409c0ed0cb3084cfa))

- Set up GitHub Pages with landing page and brand kit (#4)
  ([#4](https://github.com/platzhersh/oehrpy/pull/4),
  [`aa65777`](https://github.com/platzhersh/oehrpy/commit/aa657770be4a2da13898c83b3bc21abe475f3ac3))

### Testing

- Add integration test setup with ehrbase (#10)
  ([#10](https://github.com/platzhersh/oehrpy/pull/10),
  [`f1a2aa0`](https://github.com/platzhersh/oehrpy/commit/f1a2aa00669cf46b265a8209c9a012436de9a980))
