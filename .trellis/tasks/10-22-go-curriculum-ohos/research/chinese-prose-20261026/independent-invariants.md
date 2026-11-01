# Final independent data and mechanical audit

Status: **PASS — source/data/mechanical only**.
Snapshot: `2026-10-26T01:52:28.955069+00:00` through `2026-10-26T01:52:29.469547+00:00` (UTC).

- Frozen baseline SHA-256: `bff2607635b7121ba20070e7e104f91848f3b818166e91d396efda9e98732ee5`.
- Linter SHA-256: `4571e2c4c1c8d79062593c598999f207e390cf006f3f29a16d84107600c907cf`.
- Actual topic JSON files: 160/160.
- Canonical masked immutable hashes: 160/160 match.
- Sample byte SHA-256 values: 160/160 match.
- Per-field modality records: 2272/2272 checked.
- Actual mutable prose fields: 2272.
- Changed prose fields since frozen before: 998.
- Projection-content matches: 160/160.
- Invariant/structure errors: 0.
- Topic/sample/projection files changed during audit: 0.

## Per-owner field changes

| Topic range | Topics | Topic files changed | Mutable fields | Changed fields | Unchanged fields |
|---|---:|---:|---:|---:|---:|
| T121–T160 | 40 | 40 | 608 | 250 | 358 |
| T161–T200 | 40 | 40 | 624 | 243 | 381 |
| T201–T240 | 40 | 40 | 520 | 283 | 237 |
| T241–T280 | 40 | 40 | 520 | 222 | 298 |

## Mechanical lint

- Default40: exit `0`, findings `0`. Actual160 after projections passed as file arguments.
- Instruction25: exit `0`, findings `0`. Checked only the `480` actual source fields named objective, prompt or hint, using one stdin invocation per topic.
- No disabled rules, baseline allowance or linter modifications. Instruction findings, if present, retain the exact source topic/field mapping in the JSON report.

- Final-blank-line-only projection differences: 40. Content and heading order remain exact after permitted newline normalization.

## Method and reproducibility

Read `baseline.json` and every actual topic/sample independently. For each topic, deep-copy current JSON and replace only each declared mutablePaths leaf with `<MUTABLE_CHINESE_PROSE>`. Hash `json.dumps(masked, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")` and compare the frozen immutableSha256. Count each baseline modality string at its original field route. Hash sample bytes directly.

Parse each before projection in baseline route order. Reverse exactly one Windows write-time CRLF conversion; preserve literal CRLF teaching content. Compare every current mutable string with its original projected string. Produce changed-field counts from those comparisons, independently of whole-file formatting. Reconstruct after projections from the exact current string values and expected route headings. Allow only Windows newline conversion and terminal blank lines when comparing the projection.

Run `python scripts/ste-lint-zh.py --json <all160 after projections>` for default40. For each topic independently, reconstruct a stdin projection from only source fields whose final route component is objective, prompt or hint. Run `python scripts/ste-lint-zh.py --json --max-chars 25` on each topic stdin. Independent documents must not be concatenated into one lexical-synonym scope. Topic/field headings identify any finding. Re-read every captured topic, sample and projection at the end; no captured bytes changed during this audit.

`independent-invariants.json` contains all160 topic SHA-256 values, all160 sample SHA-256 values, every mutable-field before/after hash, exact lint results and the source snapshot timestamps. Later edits require another audit.

## Findings

No data, structure, sample-byte, per-field modality or projection-content mismatch found.

No mechanical lint finding remains. The JSON report retains all160 instruction-lint invocation results.

## Scope and limits

This audit checks source invariants and mechanical Chinese rules. It does not prove semantic correctness, one-action compliance beyond mechanical detection, SDK/native/runtime behavior, package provenance or actual OHOS acceptance. Semantic cross-review remains a separate report. No topic JSON, sample or projection was edited. No runtime, compiler, SDK, native, WSL, device, channel or Git operation ran. Root-final artifacts were not modified.

## Current topic SHA-256 inventory

| Topic | SHA-256 |
|---|---|
| T121 | `589f316caae8107370489d560d0eb5ae311714a515e9fd5fb8fa474beeb91927` |
| T122 | `3d19ca655766f72ca50727f2fa16cf8d166acc6f712158b985959d775486115e` |
| T123 | `b3c841f8be4375a4665f984dea74ccf30ccd615ac603d7cf00fc03f496bdf15e` |
| T124 | `b3e4bdfe41527129a356f0b09104f614bd47a2622980106a61603c89a4012b38` |
| T125 | `8728fd4e35ab56d56a94410237671d602b6213afbbb956795fc2b3be78c8e022` |
| T126 | `f80871838aea3a2c93b6da3fbd78186e96f7d67dc01d2b865043265aaf2cc22e` |
| T127 | `05a8d025fabad640f8c624eaf2b48b1a48409032ea1d4e819cb582e2324ee0a4` |
| T128 | `207fc86a39d190630affe9316ca6d3343bd8b0bfae06fa85201b4431eaafcdfd` |
| T129 | `be2d45bd8761b287c3970cbb1fe58bb19131f8611e0d41788e5eeebdb0c57946` |
| T130 | `fca9743de28324db5cc9190b3991bb11309d4fa9a41b17a1212332ef9d07158e` |
| T131 | `4ed44d2e0d0a5b445c6c99962b0f7c1b86fecbba001e31e7a1a89c6a9bfd0ccd` |
| T132 | `6d4203d3710427167a365a051c3861b58193456ff912f8e52e9e9a1b26801446` |
| T133 | `71c6a85cae897a8056e07eb560c726858c501aed0e77f068da2fb5b61d974781` |
| T134 | `580040f8b1617054f19c6e24b14b3ed00effaf30f1809f1f93f32aecdf75290f` |
| T135 | `34ec452ad466329f20db7101c91d17866bb6a4e5284739970413d96fee776a0a` |
| T136 | `1257cb65cf697591dabfdf34d298ef5113cc2fcaa6819987b716651f03d427ed` |
| T137 | `3129da05160ccbdd02d6a66e9970e472c67fd165396c7e998ff4a5fe0d87d753` |
| T138 | `408e04d7a0ccb07de2efc1c7370d44eda6d65f1ac33849a1d47062963fdd1930` |
| T139 | `7a1b23f93fc68aee6d97df65dd3d3ffb4f3439036b20adb6a772d7b755cc5f15` |
| T140 | `2cb7e0308e2879ef761974cf83bcd0787357a6588e258fce392b39ce5b90602e` |
| T141 | `f2861038b2d06e650615b245227aaf6229ec6ce6b090e8cd0b568f7642360acf` |
| T142 | `1221c2e8e1c8deee7290c1c68a8e7411fe8919edd13d8727e67cb4c1a32eb8d2` |
| T143 | `1adb2a4cdad52332d436817e6c5f57c3f555f7896721578f84f3e5d1b7387746` |
| T144 | `7e756dacc93bda87fce794f7b6ecd7e58dacc2609fea066311373ef629a818d6` |
| T145 | `a3e801d4f0769e7ea803cbdb5f3c3d89e44ddb92efaf8320070c5cf873243149` |
| T146 | `14f2819f586b02b4bea59bd1bde6eb819a2eabdf23de0eca1cfe54b84cf08730` |
| T147 | `44409c87c92c5d1afd4bb3f290e826a67ebcc6c32c7f298f8cab9c2c33c48264` |
| T148 | `31c4f7dd06023948a21570155aaa9ceb95ea1188d657259cc5d2b86bea9f3e90` |
| T149 | `11846fafaaf1174c2f57116b304fe43b47d0a876afc884b02bc592bc94645c7f` |
| T150 | `215212efe36ec0316ba70041b10e6be3c240a7440c67637774eb7390b2bbc909` |
| T151 | `dd6519ceaa6f67a04814ba594ae9ea9c3f470521e1b72201f6804774e56f4e0e` |
| T152 | `728b299769d84681e0a0eb3fcf3bcce0e60b705f029c236a2e97f7ea8d7d3471` |
| T153 | `22a430fea531611db71ad4231ea10e586a70dba99caba14d637ef3ab247469b2` |
| T154 | `fb588be228530c2aed13c30e6e6eff12c238cb855b0cb54282e7b976aad7efda` |
| T155 | `e25daf2f437dfde3fbd630c4b42ff446c5e487873e335454083c9a1ea39a4429` |
| T156 | `1ce76f3a0e6c117dc902c04a463d51476b6ffc371f8f7bdd5972819065030bc5` |
| T157 | `8d17f2c0964e0a6238a0a6157e5df751d19e48dbdc76015432e2ac209c5928fa` |
| T158 | `09793220a9b37f22a24d4a9048ea83299cecd2ef835244040489ea627ecf821c` |
| T159 | `22529d59236093c14da8ef9c1389388b3ca1969e6483d30c9cd7bc4bcf181d09` |
| T160 | `86f851eff2575cc2edea7310df787b5f3fddecc1699ea6578da92c81d0e1e8f9` |
| T161 | `12f109a530b15177b93d97507a4c9be40b7cba4efeabee8134caef8e1dd5a297` |
| T162 | `73cec05f5c181bd1cc430175a5c1846f9a22d0611de70cd5404ccceddfdb7cb3` |
| T163 | `fa828190c0ff1814186fc2514cad32125bcfee89486e9c0a7ca6804eccec7dba` |
| T164 | `c86ae7abb00d7590284cdb9532bbd6fb4e79f052498a3a7df4f864cca767db7c` |
| T165 | `054fc4de7e7c80dc611525dee882ae87f48527c3d1017ce2569d38e7d5c692b7` |
| T166 | `dbe59fdb788c7d1eaada908fe0abe694f9487675b4a327a98f9da6342b6bced9` |
| T167 | `bb5f9945775ccb983d484c160b13472a6e6e2588a8e653047df1b30e4c3d10ad` |
| T168 | `1b955aaefe44ed543da031798c490b5bfd452e215e91e54741c1852eb9048f42` |
| T169 | `7ee5f0427966853b2d94a9384dcea5beee5c76d17585f84f54604139877ae9ef` |
| T170 | `f0e46ad007f337d7c416f2178a5d248528206647bf35ff1def3a6c8d9daddb55` |
| T171 | `9031b60a769ae13811c205f5ade4ba2490abc5821759a7222ae99e31e884c96c` |
| T172 | `4ee83b3b5b56a5786954857c69fff7a06609c60632a1e187791206369d6a887d` |
| T173 | `fae754662ca184def5777ed6da4391f5999ae444905ba2dfc9911a19d5b9ac2b` |
| T174 | `8a148e49a5b815a225466acaf36b090c8b05d6787a2ed2b58a95228b535a6f35` |
| T175 | `43ef45080380bca61ed50a529002b3af188d1eadfe1ed0bbf9985a85378ec308` |
| T176 | `3b7a34c169ae4bc8acb89463a9061ddcf1578aa5d3df34fd8f51303737f7dcc0` |
| T177 | `72c805861ad9f07d575a0e7de244c3493c34d780ed59a16fd7b80cf7ba79a962` |
| T178 | `2f2a449a11e0e348a64cfab449ad06723b1763c61b006c66a59dbd59b652cf65` |
| T179 | `19326c9c39c84cbae05d2e0aeef1c8f46cf4ad84b063bf48486c73b926ed36c5` |
| T180 | `bdd70eb25bcc2d49c3896806abdd7afb053da211ce08a2478ffd3eca552d1665` |
| T181 | `131f0fec2fb2742e674e47d32cdd3bcf7fba3a8d29d7e614b259fbbb5220afb1` |
| T182 | `14286594ca3204a4aea1e2ada394f7e865f3bc9e2b07a94ca6c623a990ee654f` |
| T183 | `7deddd95a10404c87512f64b55708f8d2309028162852da92cf6a859d5dd28e0` |
| T184 | `c2d8a0d6c5e823b35549d0d46b095711b37e25cc3f915aab8b42e634fdad838f` |
| T185 | `69447ff2828a129d43407696e677ba67a97bbac93f86f5b27c8113ef9697839b` |
| T186 | `ca3b2739fd599376450e522c175c899e0d1cc1a8e2c6aae0b0184f5e21632560` |
| T187 | `5beee7569e5a6ecfdd13ec46599e98ce959c0849f9ae61ecc8cf9ea822698d7e` |
| T188 | `c795504237f99759b769d49b99fba7131069fab3f862275ea811a4e3a6d52094` |
| T189 | `d62edb3d489cff1ef56efc5177a71857e6370dc5c3a264e4392077bca782ab09` |
| T190 | `0b37cc94345a28c65116d7ac642a105a510fa6ab9916b83d2930ec23dffd9591` |
| T191 | `06d8668dd087626e8891ca76ded5bfce2c223cf80d3a8451f3e13a9c00e2b863` |
| T192 | `466ff582dbc73a8daaaece441838976d003489990b0fd22635552baa1e987785` |
| T193 | `437fdfdb97172921588174a42b4c53c405717a25fc66df0919c55d5e0ffa5ade` |
| T194 | `c43cd10f21d7b0157bc1506fff1e69870532278e3648c716b81a9b4e39a9f91f` |
| T195 | `8d4820c8e016b0167a597d67afdc49c67efd7d3425011a6fdcfaf9b638b2bcc6` |
| T196 | `b8fecc05c4469b88fd60d45befe9f9c2785b8476545e7bf48323513c35bde331` |
| T197 | `112784a97751c88bdade1b8eaf58fc9e7319d55d2d77e515123e8886f8f5943f` |
| T198 | `40ede3fda02cc55fcd274d37c7f956eb70eaf4c88b686f13718653027af4eac0` |
| T199 | `d647ab81d4131bcce4e6053cd01f16736b1930aa557fd670c98d3fc4cd26f422` |
| T200 | `f9d6a0aa4e56ec13ca4ce27816a1cec7c26244ae86ade37b1555b0a6c5308549` |
| T201 | `eca0978385b035614321c32f67440af6441e06b725f821a61fe408c51f7f821c` |
| T202 | `7d983dfb4882421cfb71940e64284be15353d4ca875d4bf82e4b3ade6cb0f6fa` |
| T203 | `90bbe2483cc4719167e98801f1bde933e8406743b48b821fbbce7f2923e34df3` |
| T204 | `11a24da712799815afdf22d44d90b4001a9a0d4454bf33a6da3558b4ca34f669` |
| T205 | `8fd324d7c28b8a430d62c62c6d9e58eb7cd8c0d8c183feb728609ad59440fe3b` |
| T206 | `11668f2d0e411e83a1cee4ca7217c5c832a45250512156123036761c3387e5cb` |
| T207 | `2cf188127f7e5e4003f1081dd542a365376d4368f27e9193802dbd6271490947` |
| T208 | `9a85cb4d9bc13fa2cf34968de289c0aba7c2ab582c47b7ddcfcc020befc9de28` |
| T209 | `5a65e0597b4cae948e7c3bfe1346e728fd96ea418d4a76de4457e919150a034e` |
| T210 | `6a8f5d7e0db7ebbc4ef245d42b67f6e18e4c8daf3303495ad3dd5c22c5638fc5` |
| T211 | `c1d8fb9f203bc297203affe8ebb503021cfbdee24fb9551be1b1dc2b40a3e8f3` |
| T212 | `82e77248791086798fac056ea2954c4cbc55e5d592a3612c7a3615d32f7be234` |
| T213 | `d1010ef73968354e35e0d9b1d52a11026d8bb9c736d55bcf40d891b0ae4b248b` |
| T214 | `75a2dc71e6bf706574d8ae8461b2dcb71f5fd6f7fd067e6d46bda4f7a33cad7f` |
| T215 | `eb4891581f7ca99cebd2954c937e81cff042107943005f8bb8d7a39914841625` |
| T216 | `3e69629d7b4c720c893da7b72f4056e1914f50342c57d58f48a6d2c7986a15af` |
| T217 | `f09f6f6d7640800f6ff4a730a122475076cb9df8ea131aefc42b9426ca213d93` |
| T218 | `38e716477fc143b7f425abd2791dd9733330acaff3b280adcc9e99303f589d42` |
| T219 | `8c5d0e808e264054ca973297f12799ee1bc70154b5fef5c220d05a6b338c69ef` |
| T220 | `97b924efb819a618efb31d954c8b0a72711813c25432bf98a1b9332235df06da` |
| T221 | `81cafe8418aa677fc93fe1393eb625c13cddfba94b2a86982266ae7d323b66b3` |
| T222 | `023d933afbeebb824d6d651dbdb42658b1ca1f8f1b40d66d331f7f5b0f66a52a` |
| T223 | `6cb85582caaa17a4d22bb170fbd761a67469f9277e750c4271eab68bac25d3ca` |
| T224 | `926cf20131c2f5dfa98da8bbe9e3cc27aeaf8c8d1a068fd0d7e211e9caf7befc` |
| T225 | `c842e5778fa72c64e83d41ffa0a868f66a1e6bd2b638bc2e65d49e6fe550d223` |
| T226 | `7084a81caf2679a3a02fc7ff74f367b49b2d023542b8e3840869fb8b9f7a6006` |
| T227 | `94085b38f91a4235e1d4fa7098eff3848677083ec016e238cf86b1cfeef15bb5` |
| T228 | `2c3ef8af8a6151c81efa479488e23b242611eeb96b81130a774a1c9ad02b80cc` |
| T229 | `198e5c966b04439bb11247ddc879ece4b4809a112ff6ed41e1c20d3088b4ca19` |
| T230 | `74decb74d6fe19867d7ba60e9b58d4c488abc2574d034ddc009ea5cbe1d114c8` |
| T231 | `b3b4547c64faacdbf7f5808c7569ed98d0232a3026f2e64dccc04557f5104786` |
| T232 | `3d80397e5e71d6afc490a568ed239e6cba76e7a0957b31180a6c6956729d8b5d` |
| T233 | `10bb55d3e59e1aefb0112c0d3d0d19d40dcfc610b65a69d0f4c323066a420f15` |
| T234 | `54c100117c7c2b31313bec704da954b29a2fdc1ae7926a246577b228c061a8ce` |
| T235 | `c847167645b16fab6b72a67db43cedda3ce9dd91c4d1bc0b52fc9294ad8a7f76` |
| T236 | `2272b3784314ad5e6681d073d587892f3879d770a3984bb99aa979ece2721a7a` |
| T237 | `2276464efe263cdec0c7e01e7619d6e8cbd60bdea260538887776a60bf9cd518` |
| T238 | `273da80a6f1d1d5f2ef3e2c73f0949d6f2af080fe6b512ba7459c28b443bfe09` |
| T239 | `e3d0e234e1d684d934b646a2e436c5d6f72cd06732a97e23711eae492a4f4bbb` |
| T240 | `151d652418bbd68e73fb5ef416c301f664efdb0a55a1805e95f5c0fe83dddb94` |
| T241 | `05575dfea73741867d98b64bec94c49e42d78a635cc0e2e12ecdac680e2cb253` |
| T242 | `17962ddf652d7c9da2d436290b9ce1bd62c69e3ecd765c73e73576d3059f32e1` |
| T243 | `d612c99f4182d5585f47dc73b101e9b65892efa0ccbb7611f972bd0bb11bec7d` |
| T244 | `7bd23ab7d71a9c112d74dbe20a8d166f3f996b54036f3614f9ad7458f46c4d5b` |
| T245 | `2165280a6752ae0bd29622cfbf39f6259e8e114914a29997ed20cdc2e3f6df0b` |
| T246 | `efaa4bc53beef4df680b74fe95136038a82775b2233af0803f018f1c37a7312a` |
| T247 | `730031ce98c76ab7313627e188ca57e7f633aab5180aa15515e0196113b42c5d` |
| T248 | `0cdd95cc425ac2beebc02bb004dbc5e35f78e150e85d1c5778a80e310bbe258e` |
| T249 | `ee99fd02d7bc86ddc18fea42bb89d352f768963db845153b0435900464061837` |
| T250 | `ab04b490335626fd452a637cc7adba5a7651fe41609d745a01696b16e2aeab6b` |
| T251 | `0903f54f0b7709317f4c238d51e49d9b02afcb391d5afc6ce802af8513e1c8d4` |
| T252 | `27e8578fec67083883ebf7fad1c3cd305e83c4d97d7cdd8bbd01cc0c06cd249e` |
| T253 | `7e6059b7b4da56fd5d9be13ce395bfd5ad8c480c1e66a5ccfc47c78bdae8e726` |
| T254 | `dd3e5d35208829075ed410b6609661bf9c6caa1221a4bd52dd835fe58c413169` |
| T255 | `5870421dce22be92ea8463aaa573757f6a8b39edc1369fe81cc55a20049963a7` |
| T256 | `a8be89a00bd006b5b4bb2f0ef06e83499d9297b5d331746ddcf825ef98fd32f0` |
| T257 | `0e01ba9454a34fe2f439f478256f4b787c5bcae1b8b21efaeb7ecf74d38408dc` |
| T258 | `6dc4f1cbbde14d38689e0e74f1e12dc94b35e3a0e1c780e6a720ca38906a2c83` |
| T259 | `811e55dd6614ae389d968104e40307a33ec6f54466e916941bea655db5608422` |
| T260 | `10a0fe857b0067887169f4b95a6a98c0382cddffff309c372f130528dc9b3a9b` |
| T261 | `d62f731419598eb53bb56e33ccf6a9e4b9a15f29835c8799fe0c78b9b18d9618` |
| T262 | `e1e229388e92ad320586a2d4dbd457e019c47845efb5d1a77ff30cbcdcfd5aea` |
| T263 | `f7076a893f6aa1283887185ce15469db206d1211fc46991d12092854c1543569` |
| T264 | `b0483f3c36a0e51dce452c75052ba4e49e7f6f64adf3e12c263391e07cf14683` |
| T265 | `d67de2a109ed3983af87db2debc1851cae78b61543a946cbf94d14f9ddbd1296` |
| T266 | `55710adb386576a5d4c0a073dd6078ee0da7cf930948996d9fa374b37461ba6d` |
| T267 | `5c48a55b8dc305c3313b4b2bb2d62118c7e9ba8ef61231e0af68c4e688948ce0` |
| T268 | `c60f84a3bf58d297b463243a97a51999f4000cce05f71368f17dbdafd0e4f31d` |
| T269 | `c5e40e6e3d5b2da660a8331c9c02fbcc4dc3faf8e3c9f7b934cef2af0b47a321` |
| T270 | `1344d6f0ddaeeca93e62dfc0d96d4655a336bd5b2360caa92bafec06db7c4836` |
| T271 | `5b037eb004d7fc648c64a3e87146163f9d494230e94d46d142a4215a1425ccd3` |
| T272 | `ee110358141a5f0e7eba7ed5f562878d482acce6524ec9cbc34cda007b0cd352` |
| T273 | `94fe848ae182e98c007cf38dd163c7c8cab7a6c2979f44fbeef3dabb10993152` |
| T274 | `982b6bc3ebe4c7702d9ea8eed7979082b2415ee59cedc519e31225d81c34157c` |
| T275 | `32ec15ecc36b2e53d3868917a4a570e486975dff6afcd95aadc058e24ef284aa` |
| T276 | `0645535fa87e651ea870a214a3003be5b9062b94d11c3cf4bf24da3774f8ed48` |
| T277 | `a714a4447bc5ecb20b3b0978ddba91862139820cce2b0cb9f0ce12033e7d6a8d` |
| T278 | `b7a6c8824f3e4fb5dadc5ddfc744f588a926dd73c5e98139294b1b8ef096decc` |
| T279 | `7759200de697be43a1b01e658efbf0517fe94623ff01a4b24de0c13c778205ea` |
| T280 | `949a1c755fd8d8bb9ffcafc4e38e5bbf6fb6cf55c451d075cfca5c3fdbb16c3b` |

Instruction25 verification completed at `2026-10-26T01:56:11.539753+00:00` UTC. Re-read all160 actual topic hashes after the160 lint invocations: 0 changed.

## Read-only spec review

Reviewed the new `Controlled Chinese prose contract (2026-10-26)` section in `.trellis/spec/backend/go-curriculum-tooling.md`, file SHA-256 `edabb58c151ce7f559a5107d85d3516b28a4bdf5f8e3783845031a8effc25299`. **PASS**: no inaccurate acceptance, preservation or runtime claim found. Its canonical hash, modality, sample, projection and semantic boundaries match this audit. Its basis-point,1024²,duplicate-group and patch-key examples match the source review.

Operational clarification: use a single topic/document as each instruction-lint invocation scope. Concatenating160 independent topics creates cross-document synonym findings and is not valid evidence of term inconsistency. The audit uses160 separate stdin invocations without disabling any rule.

Final recheck at `2026-10-26T01:58:13.001317+00:00` UTC re-read all160 topics,160 after projections and160 samples against the captured SHA-256 inventory: **0 changed files**. Root-final and spec files were not edited.
