# CHANGELOG


## v0.17.0 (2026-10-09)

### Bug Fixes

- **templates**: Set vital signs time via history_origin (#87)
  ([#87](https://github.com/platzhersh/oehrpy/pull/87),
  [`51a3e10`](https://github.com/platzhersh/oehrpy/commit/51a3e105491366e2c75e8daff376d0dc0e0ddac4))

- **website**: Add ico/png favicon fallbacks (#93)
  ([#93](https://github.com/platzhersh/oehrpy/pull/93),
  [`815aa97`](https://github.com/platzhersh/oehrpy/commit/815aa971e7d7e065d6e849d303273b1931c869ab))

- **website**: Load oehrpy wheel in validator without micropip (#78)
  ([#78](https://github.com/platzhersh/oehrpy/pull/78),
  [`86e5d7c`](https://github.com/platzhersh/oehrpy/commit/86e5d7cb76efeb9c540fbeb4a92724ef28409448))

- **website**: Menu button header nav on small screens (#83)
  ([#83](https://github.com/platzhersh/oehrpy/pull/83),
  [`f3ed997`](https://github.com/platzhersh/oehrpy/commit/f3ed997bb4329ea3ab039f8f9b60556beee15f3c))

- **website**: Square favicon and brand kit header/footer (#81)
  ([#81](https://github.com/platzhersh/oehrpy/pull/81),
  [`1cb1e1a`](https://github.com/platzhersh/oehrpy/commit/1cb1e1a6854f0f096448aff6d5fd7105b473ada4))

### Build System

- **deps**: Bump picomatch from 2.3.1 to 2.3.2 in /vscode-extension (#46)
  ([#46](https://github.com/platzhersh/oehrpy/pull/46),
  [`9e5adaf`](https://github.com/platzhersh/oehrpy/commit/9e5adaf0bf1f916f73e00e3435096cf4f7ef7703))

- **deps-dev**: Bump brace-expansion from 1.1.12 to 1.1.21 in /vscode-extension (#91)
  ([#91](https://github.com/platzhersh/oehrpy/pull/91),
  [`ca3ffba`](https://github.com/platzhersh/oehrpy/commit/ca3ffba76fa45a33a427b793a19900bad54101cf))

- **deps-dev**: Bump flatted from 3.4.1 to 3.4.2 in /vscode-extension (#47)
  ([#47](https://github.com/platzhersh/oehrpy/pull/47),
  [`931ff22`](https://github.com/platzhersh/oehrpy/commit/931ff221a1f89c1e9a47f10215505566749cd193))

- **deps-dev**: Bump form-data from 4.0.5 to 4.0.6 in /vscode-extension (#64)
  ([#64](https://github.com/platzhersh/oehrpy/pull/64),
  [`320a2fb`](https://github.com/platzhersh/oehrpy/commit/320a2fbf30d2f63364d67c10c400574eb2ee79f9))

- **deps-dev**: Bump markdown-it from 14.2.0 to 14.3.2 in /vscode-extension (#92)
  ([#92](https://github.com/platzhersh/oehrpy/pull/92),
  [`3f350eb`](https://github.com/platzhersh/oehrpy/commit/3f350eb5ae39c411aa31ef528b48db45efccbca1))

- **deps-dev**: Bump tmp from 0.2.5 to 0.2.7 in /vscode-extension (#48)
  ([#48](https://github.com/platzhersh/oehrpy/pull/48),
  [`bdd2912`](https://github.com/platzhersh/oehrpy/commit/bdd291220efa783833ca2b4dd1158ab8e86c03e8))

- **deps-dev**: Bump undici from 7.23.0 to 7.30.0 in /vscode-extension (#90)
  ([#90](https://github.com/platzhersh/oehrpy/pull/90),
  [`9c6cc50`](https://github.com/platzhersh/oehrpy/commit/9c6cc5087d31f2cb0028f6837d077768b0079eeb))

### Continuous Integration

- **release**: Cut releases on demand instead of on every push (#80)
  ([#80](https://github.com/platzhersh/oehrpy/pull/80),
  [`b3176cd`](https://github.com/platzhersh/oehrpy/commit/b3176cd95a3d340f0f0995c1e0421fa6d80c2ef4))

### Documentation

- Add end-to-end FLAT example (RM values to FLAT to CDR) (#88)
  ([#88](https://github.com/platzhersh/oehrpy/pull/88),
  [`7dc4062`](https://github.com/platzhersh/oehrpy/commit/7dc4062b82962397dcddd036fc0ca24560c29cc4))

- Add per-CDR feature support matrix (#89) ([#89](https://github.com/platzhersh/oehrpy/pull/89),
  [`f33f3bf`](https://github.com/platzhersh/oehrpy/commit/f33f3bf4cb2538c2689e2635665c67708815e20d))

### Features

- **client**: Add ferroehr support via generic its-rest client (#86)
  ([#86](https://github.com/platzhersh/oehrpy/pull/86),
  [`080d0e9`](https://github.com/platzhersh/oehrpy/commit/080d0e9f08e5bc0ff0d39342ff6b19cf2347cb7e))

- **client**: Add get_template_example with detail_level and type (#84)
  ([#84](https://github.com/platzhersh/oehrpy/pull/84),
  [`a45ad03`](https://github.com/platzhersh/oehrpy/commit/a45ad03e7615bf56d7d549ef8e0405651e6270e4))

- **website**: Add hero badges and footer copyright note (#85)
  ([#85](https://github.com/platzhersh/oehrpy/pull/85),
  [`5008619`](https://github.com/platzhersh/oehrpy/commit/5008619d4a85e3f1ef310885087abe3ae3efe6be))

- **website**: Seo improvements for oehrpy.dev (#82)
  ([#82](https://github.com/platzhersh/oehrpy/pull/82),
  [`9b5bf47`](https://github.com/platzhersh/oehrpy/commit/9b5bf4725ced35dca53f2ce7f38586ee5999f4b4))


## v0.16.1 (2026-09-24)

### Bug Fixes

- **website**: Serve from oehrpy.dev root and retire old docs site (#79)
  ([#79](https://github.com/platzhersh/oehrpy/pull/79),
  [`d383fb7`](https://github.com/platzhersh/oehrpy/commit/d383fb7554948513f187a4d403ca992b61c5f9f3))

### Continuous Integration

- Bump github actions off deprecated node 20 runtime (#77)
  ([#77](https://github.com/platzhersh/oehrpy/pull/77),
  [`2672ef8`](https://github.com/platzhersh/oehrpy/commit/2672ef852ebb693ee85ac91531c3820e0ea0b9f4))


## v0.16.0 (2026-09-24)

### Build System

- **deps**: Bump markdown-it and @vscode/vsce in /vscode-extension (#62)
  ([#62](https://github.com/platzhersh/oehrpy/pull/62),
  [`491ca0b`](https://github.com/platzhersh/oehrpy/commit/491ca0b58737f7242da6f3eb0450b6de64914068))

- **deps-dev**: Bump qs from 6.15.0 to 6.15.2 in /vscode-extension (#50)
  ([#50](https://github.com/platzhersh/oehrpy/pull/50),
  [`780f54f`](https://github.com/platzhersh/oehrpy/commit/780f54f0961fc8eb47c4de723e93086d0795eacf))

### Documentation

- Add star history, downloads badge, related project links (#75)
  ([#75](https://github.com/platzhersh/oehrpy/pull/75),
  [`93a6866`](https://github.com/platzhersh/oehrpy/commit/93a68660d54a19f43e7f2eeef13c960f2cd1fc6b))

### Features

- **website**: Migrate github pages site to astro (#76)
  ([#76](https://github.com/platzhersh/oehrpy/pull/76),
  [`6f25429`](https://github.com/platzhersh/oehrpy/commit/6f25429eeb1ed7f9f6c3228106ffbf545fd1db8d))


## v0.15.0 (2026-06-03)

### Features

- **vscode**: Add OPT template validation (Phase 3E) (#60)
  ([#60](https://github.com/platzhersh/oehrpy/pull/60),
  [`dc13532`](https://github.com/platzhersh/oehrpy/commit/dc13532f6398ec76c15fdbe7fe00b1de45214780))


## v0.14.1 (2026-06-01)

### Bug Fixes

- **vscode**: Validate in-process + add oehrpy.validation CLI (#59)
  ([#59](https://github.com/platzhersh/oehrpy/pull/59),
  [`4491765`](https://github.com/platzhersh/oehrpy/commit/4491765072153e898e32fbf777f3bbccb5a4a9d4))

### Testing

- **vscode**: Expand Web Template tree parsing unit tests (#58)
  ([#58](https://github.com/platzhersh/oehrpy/pull/58),
  [`ea00256`](https://github.com/platzhersh/oehrpy/commit/ea00256a812599cee83e11e8c1279926a36a032a))


## v0.14.0 (2026-06-01)

### Build System

- **deps**: Pin dependencies to exact versions and drop unused extras (#53)
  ([#53](https://github.com/platzhersh/oehrpy/pull/53),
  [`0c941ee`](https://github.com/platzhersh/oehrpy/commit/0c941eefbbe369120994a2520f8df1b2c94b8aef))

### Features

- **vscode**: Add Web Template tree view to Explorer sidebar (#55)
  ([#55](https://github.com/platzhersh/oehrpy/pull/55),
  [`aef2e1e`](https://github.com/platzhersh/oehrpy/commit/aef2e1e1b3c2cf87c536a7a414b17215758af4ac))


## v0.13.0 (2026-05-31)

### Features

- **vscode**: Add FLAT path autocomplete from Web Template (#52)
  ([#52](https://github.com/platzhersh/oehrpy/pull/52),
  [`10b2ee7`](https://github.com/platzhersh/oehrpy/commit/10b2ee7a2d2e2415bcf8150866bddbe9074f9e03))


## v0.12.0 (2026-05-31)

### Features

- Add VS Code extension for FLAT format validation (#25)
  ([#25](https://github.com/platzhersh/oehrpy/pull/25),
  [`c71deb9`](https://github.com/platzhersh/oehrpy/commit/c71deb9c82f4c7378a38dea64ab982bf24377d2d))


## v0.11.0 (2026-05-31)

### Features

- **docs**: Improve GitHub Pages SEO (#44) ([#44](https://github.com/platzhersh/oehrpy/pull/44),
  [`e8b8aec`](https://github.com/platzhersh/oehrpy/commit/e8b8aec0493949abdc78dfd543102d7753076d86))


## v0.10.0 (2026-05-31)

### Features

- **client**: Add contribution support (PRD-0003) (#43)
  ([#43](https://github.com/platzhersh/oehrpy/pull/43),
  [`15be69b`](https://github.com/platzhersh/oehrpy/commit/15be69bfa7a7da8d72a4acb3b7bf0042e3dbc922))


## v0.9.0 (2026-04-11)

### Features

- Rename package from openehr_sdk to oehrpy (#40)
  ([#40](https://github.com/platzhersh/oehrpy/pull/40),
  [`6b9b835`](https://github.com/platzhersh/oehrpy/commit/6b9b835e2a679d4497342e65f3827235cc0446e5))


## v0.8.1 (2026-04-11)

### Bug Fixes

- Add fallback to admin API for EHRBase 2.x template deletion (#39)
  ([#39](https://github.com/platzhersh/oehrpy/pull/39),
  [`88a985e`](https://github.com/platzhersh/oehrpy/commit/88a985e68bbda001bac595349465e13e37a4ac99))


## v0.8.0 (2026-04-10)

### Features

- Add template management methods (PRD-0013)
  ([`03c11e8`](https://github.com/platzhersh/oehrpy/commit/03c11e8c878907970ccb12c1915bfe51d6cbd210))


## v0.7.0 (2026-04-04)

### Documentation

- Add openEHR workflow diagram page and PRD-0012 (#36)
  ([#36](https://github.com/platzhersh/oehrpy/pull/36),
  [`3b36429`](https://github.com/platzhersh/oehrpy/commit/3b36429cc754869785d9c19369a880962095edff))

### Features

- Add ADR-0005 Web Template as primary source for FLAT paths (#37)
  ([#37](https://github.com/platzhersh/oehrpy/pull/37),
  [`6ffa144`](https://github.com/platzhersh/oehrpy/commit/6ffa144847a07e762d121a7454af1dbd668ceca1))


## v0.6.2 (2026-04-04)

### Bug Fixes

- **validation**: Accept ctx/ shorthand paths in FlatValidator (#35)
  ([#35](https://github.com/platzhersh/oehrpy/pull/35),
  [`9cac026`](https://github.com/platzhersh/oehrpy/commit/9cac0261679280fa569108423773bd84ed91ee23))


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
