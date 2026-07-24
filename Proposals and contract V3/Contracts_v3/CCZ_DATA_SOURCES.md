# CCZ PATH C - OPEN NODULE ABUNDANCE SOURCE HUNT INDEX
Purpose: Locate non-confidential, published CCZ polymetallic-nodule abundance
observations outside ISA DeepData and turn them into an ingestion queue for the
CCZ Prospectivity Engine.

Prepared: 2026-07-19
Scope: Station-, event-, box-core-, image-frame-, and grid-level nodule abundance,
plus metal-grade datasets that can be joined to abundance observations.

## IMPORTANT DISTINCTION
This catalog separates five different kinds of evidence:

  [MASS]   Measured nodule mass or concentration, normally kg/m2.
  [COUNT]  Nodule count or density, normally nodules/m2.
  [COVER]  Visible nodule cover from images, normally percent cover.
  [GRID]   Regional compiled/interpolated abundance points or rasters.
  [GRADE]  Chemical composition that can be joined to an abundance station.

Access/work flags:

  [NOW]       Directly downloadable numeric data. Ingest first.
  [DERIVE]    Numeric observations are open, but kg/m2 must be calculated.
  [SUPP]      Values are in supplementary files attached to a paper.
  [DIGITIZE]  Values are exposed mainly through figures, maps, or tables in PDF.
  [CONTACT]   Primary investigators clearly possess the observations, but the
              full station table is not openly exposed in the located source.
  [HUB]       A source directory, archive, report list, or spatial reference.
  [DUPLICATE] Likely overlaps another dataset in this catalog.
# 
# TIER 1 - INGEST NOW: DIRECT NUMERIC ABUNDANCE OR DERIVABLE SAMPLE DATA

[01] PANGAEA - SO268 box-core nodule summary
Status: [NOW] [MASS] [COUNT] [COVER]
Link:   https://doi.org/10.1594/PANGAEA.904967
What:   Station/event coordinates, nodule counts, buried counts, median size,
        total recovered mass, and visible cover from 50 x 50 cm box cores in
        BGR and GSR areas during SO268/1 and SO268/2.
Use:    The reported total nodule mass can be converted to kg/m2 by multiplying
        by 4 because each box core sampled 0.25 m2. This should be the first
        modern contractor-area table loaded into the database.
Work:   Download the tab-delimited file, preserve original mass units, calculate
        abundance_kg_m2, and retain expedition, event, latitude, and longitude.
License: CC BY-NC 4.0.

[02] PANGAEA - DOMES floor-density measurements, Fewkes et al. (1980)
Status: [NOW] [MASS]
Link:   https://doi.org/10.1594/PANGAEA.878220
What:   Direct box-core nodule floor-density measurements in kg/m2 from the
        DOMES A, B, and C study sites, with event coordinates and station data.
Use:    High-value historic station-level training data with an already
        normalized abundance field.
Work:   Download and ingest; standardize site names and inspect wet/dry basis.
License: CC BY 3.0.

[03] PANGAEA - DOMES abundance and seafloor observations, Piper et al. (1979)
Status: [NOW] [MASS] [COVER]
Link:   https://doi.org/10.1594/PANGAEA.880886
What:   Event coordinates, nodule concentration in kg/m2, percent coverage,
        size, texture, and deposit descriptions for hundreds of DOMES records.
Use:    Direct historic mass-abundance observations plus morphology and cover
        fields for model features and method comparison.
Work:   Download and ingest; compare events against [02] before deduplication.
License: CC BY 3.0.

[04] PANGAEA - DOMES Site C nodule size and weight, Sorem (1989)
Status: [DERIVE] [MASS] [COUNT]
Link:   https://doi.org/10.1594/PANGAEA.879534
What:   Station/event coordinates and nodule size/weight observations from box
        cores at DOMES Site C.
Use:    Reconstruct sample-level total mass and size distribution. If sampler
        area is recorded in the source metadata, derive kg/m2.
Work:   Group individual records by event, sum mass, verify box-core area, then
        compare with [02] and [03] for overlapping stations.
License: CC BY 3.0.

[05] PANGAEA - SO268 individual nodule measurements
Status: [DERIVE] [MASS] [COUNT]
Link:   https://doi.org/10.1594/PANGAEA.904962
What:   Approximately 9,000 individual nodules with length, width, height,
        mass, station/event coordinates, and SO268 expedition metadata.
Use:    Derive event-level count, recovered mass, mean nodule mass, size-class
        distributions, and morphology predictors. Join to [01] by event.
Work:   Aggregate by event; do not treat individual nodules as independent
        spatial samples.
License: CC BY-NC 4.0.

[06] Dryad - CCZ benthic-chamber experiments and nodule abundance
Status: [NOW] [MASS] [DERIVE]
Link:   https://doi.org/10.5061/dryad.tdz08kq6w
What:   Open Excel files from in-situ chamber experiments, including nodule
        abundance, total nodule surface area, average nodule surface area, and
        experimental measurements at several CCZ sites.
Use:    Provides additional sample/experiment-level nodule abundance and surface
        area relationships outside the classic mining-resource datasets.
Work:   Inspect workbook sheets for station identifiers and coordinates; retain
        the chamber footprint and do not merge experimental replicates blindly.
License: See the Dryad record.

[07] Durden et al. - APEI-6 box-core nodule density
Status: [NOW] [COUNT] [DIGITIZE]
Link:   https://doi.org/10.1007/s12526-017-0636-0
Open copy: https://pmc.ncbi.nlm.nih.gov/articles/PMC6979535/
What:   Reports nodule characteristics from 17 box cores of 0.25 m2 in APEI-6,
        including a mean surface density of 338 nodules/m2 and nodule dimensions.
Use:    A direct sample-based count-density result in a protected reference
        area. Individual-core values may require supplementary-material hunting
        or author contact if not tabulated in the article.
Work:   Capture cruise JC120, location, box-core count, footprint, mean, standard
        error, and any per-core values exposed in tables or supplements.

[08] PANGAEA - Deep Sea Ventures / R.V. Prospector 1976 observations
Status: [NOW] [COUNT] [MASS] [DIGITIZE]
Link:   https://doi.org/10.1594/PANGAEA.871493
What:   Migrated NOAA/MMS legacy CCZ box-core and seafloor observations from
        Deep Sea Ventures exploration aboard R.V. Prospector.
Use:    Historic station coordinates and nodule quantity/descriptive fields;
        potentially useful numeric or ordinal abundance after schema inspection.
Work:   Download and classify each quantity field as numeric, categorical, or
        qualitative. Cross-check against NOAA/NCEI mirrors in Tier 5.

[09] PANGAEA - Fewkes et al. DOMES dataset series
Status: [HUB] [DUPLICATE]
Link:   https://doi.org/10.1594/PANGAEA.878223
What:   Parent publication series connecting DOMES floor density, geochemistry,
        and an original camera-abundance document.
Use:    Provenance and duplicate control for [02], plus access to related image
        abundance and chemistry components.
Work:   Use as a dataset-family record, not as a new independent sample set.

[10] PANGAEA - Piper et al. DOMES dataset series
Status: [HUB] [DUPLICATE]
Link:   https://doi.org/10.1594/PANGAEA.880888
What:   Parent series linking the Piper DOMES abundance and chemistry tables.
Use:    Discover all related child datasets and preserve publication lineage.
Work:   Do not double-count child datasets as independent observations.
# 
# TIER 2 - OPEN IMAGE-FRAME COVER, COUNT, AND GEOREFERENCED SEAFLOOR DATA

[11] Amon et al. 2016 - UK-1 and EPIRB image-frame nodule data
Status: [SUPP] [COUNT] [COVER]
Article: https://www.nature.com/articles/srep30492
Open copy: https://pmc.ncbi.nlm.nih.gov/articles/PMC4965819/
What:   Supplementary Table S3 contains image-frame measurements from UK-1 and
        EPIRB, including nodule counts/density, exposed plan area, and percent
        cover. The study analyzed 241 frames and tens of thousands of nodules.
Use:    Strong frame-level cover/count training data and a bridge between image
        metrics and physical box-core abundance.
Work:   Download all supplements, retain frame geometry and survey stratum, and
        keep image-derived metrics separate from recovered mass.

[12] PANGAEA - APEI-6 nodule-cover gradient, Simon-Lledo et al.
Status: [NOW] [COVER]
Link:   https://doi.org/10.1594/PANGAEA.893220
What:   Georeferenced AUV/image-derived nodule cover and ecological measurements
        across a nodule-cover gradient in APEI-6.
Use:    Direct spatial proxy observations for prospectivity and habitat layers.
Work:   Ingest as image-derived cover, not kg/m2; preserve transect/image IDs.

[13] PANGAEA - SO268 georeferenced seafloor-image series
Status: [NOW] [COVER] [DERIVE]
Parent: https://doi.org/10.1594/PANGAEA.935856
Example child 1: https://doi.org/10.1594/PANGAEA.935889
Example child 2: https://doi.org/10.1594/PANGAEA.935887
What:   Georeferenced OFOS imagery from undisturbed and disturbed CCZ sites in
        BGR and GSR areas during SO268.
Use:    Run computer vision or manual annotation to estimate percent cover,
        nodule count, size class, and spatial patchiness.
Work:   Download image metadata first, then select non-overlapping frames and
        calibrate pixel area before estimating cover.

[14] Mendeley Data - GSR collector-test site nodule coverage
Status: [NOW] [COVER]
Link:   https://data.mendeley.com/datasets/7jst5wyc6j/1
What:   Open data and R scripts containing megafauna, depth, and polymetallic
        nodule coverage across a GSR MiningImpact collector-test area.
Use:    Modern GSR-area spatial cover observations and reproducible analysis.
Work:   Ingest raw cover and coordinates; separate pre-impact, impact, and
        post-impact records.
License: CC BY 4.0.

[15] Zenodo - south-central CCZ environmental-driver data, KIOST
Status: [NOW] [COVER] [HUB]
Link:   https://zenodo.org/records/17395318
What:   Raw data supporting a KIOST study of megafaunal biodiversity and
        environmental drivers in the south-central CCZ.
Use:    Inspect all files and paper supplements for nodule cover or abundance
        covariates tied to KIOST stations; at minimum it is a station crosswalk.
Work:   Verify whether nodule metrics are raw observations or inherited rasters.

[16] Zenodo - Abyssal NE Pacific Seafloor Megafauna Dataset
Status: [NOW] [COVER] [HUB]
Link:   https://zenodo.org/records/7982462
What:   Large standardized image-observation dataset spanning multiple CCZ
        cruises and contract areas.
Use:    Station/image crosswalk and potential nodule-cover covariates; useful for
        aligning ecological image surveys with abundance sources.
Work:   Inspect environmental fields and linked survey metadata before deciding
        whether nodule values are independent observations.

[17] Zenodo - DeepCCZ synthesis and nodule-size documentation
Status: [NOW] [COUNT] [HUB]
Link:   https://doi.org/10.5281/zenodo.4214934
What:   Open DeepCCZ synthesis files, including a nodule-size and epizoan
        documentation PDF and linked code/data repositories.
Use:    Potential nodule size/count metadata and a cross-cruise station map.
Work:   Treat biological files as ancillary; extract only independently observed
        nodule measurements and provenance.
# 
# TIER 3 - REGIONAL ABUNDANCE GRIDS, MAPS, AND HISTORIC COMPILATIONS

[18] ISA Technical Study No. 6 - CCZ geological model
Status: [GRID] [DIGITIZE]
Direct PDF: https://www.isa.org.jm/wp-content/uploads/2022/04/GeoMod.pdf
Legacy PDF: https://ran-s3.s3.amazonaws.com/isa.org.jm/s3fs-public/files/documents/tstudy6.pdf
Book record: https://books.google.com/books/about/A_Geological_Model_of_Polymetallic_Nodul.html?id=51eW6dOYnQwC
What:   The central historic compilation of CCZ nodule abundance and metal-grade
        information used by later resource studies. It includes point/grid data,
        maps, and the geological resource model.
Use:    Build a regional 0.5-degree abundance/grade layer and trace older source
        references back to their original cruises.
Work:   Extract tables first; georeference and digitize maps only where numeric
        tables are absent. Mark all records as compiled rather than raw samples.

[19] Washburn et al. 2021 - regional CCZ environmental/resource data
Status: [SUPP] [GRID]
Link:   https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2021.661685/full
What:   Regional nodule abundance and Co/Ni/Mn/Cu grade values, largely derived
        from ISA Technical Study No. 6 with additional Charles Morgan values,
        distributed as 0.5-degree points and supporting rasters/supplements.
Use:    Fastest path to a machine-readable regional resource layer.
Work:   Download supplementary material; record each point's inherited source.
        Do not label these grid points as independent station samples.

[20] GRID-Arendal - CCZ nodule abundance map
Status: [GRID] [DIGITIZE]
Link:   https://www.grida.no/resources/7354
What:   High-resolution regional map showing spatial variation in nodule
        abundance across the CCZ.
Use:    Visual validation and possible raster digitization where the legend and
        projection are recoverable.
Work:   Prefer [18] or [19] numeric data; use this map as a cross-check.

[21] USGS Open-File Report 78-814 - northeastern equatorial Pacific
Status: [GRID] [DIGITIZE]
Link:   https://doi.org/10.3133/ofr78814
USGS page: https://www.usgs.gov/publications/manganese-nodule-resources-northeastern-equatorial-pacific-0
What:   Historic regional manganese-nodule resource assessment with maps,
        assumptions, and a bibliography of source cruises.
Use:    Find pre-ISA data sources and reconstruct older abundance contours.
Work:   Digitize only after checking whether cited station tables exist in NOAA,
        Scripps, or PANGAEA.

[22] USGS Bulletin 1689-A - Subsea Mineral Resources
Status: [GRID] [DIGITIZE]
Link:   https://pubs.usgs.gov/bul/1689a/report.pdf
What:   Regional tables and maps of nodule concentration in kg/m2, metal content,
        and depth, including a defined Clarion-Clipperton region.
Use:    Independent historic summary layer and source bibliography.
Work:   Extract tabular values and document the geographic aggregation used.

[23] AOM Area 1 Technical Report Summary
Status: [GRID] [DIGITIZE] [CONTACT]
Link:   https://www.sec.gov/Archives/edgar/data/798528/000119312526215704/d104064dex963.htm
What:   Public technical report summary based on historical pioneer-contractor,
        box-core, and ISA geological-model information; reports wet abundance
        conventions and resource-estimation assumptions.
Use:    Current commercial resource-block maps, historical source lineage, and
        conversion assumptions.
Work:   Extract maps/tables; identify appendices or named source databases that
        may support a data request.

[24] TOML Clarion-Clipperton Zone Project report
Status: [GRID] [DIGITIZE] [CONTACT]
Access lead: https://www.researchgate.net/publication/309315120_TOML_Clarion_Clipperton_Zone_Project_Pacific_Ocean
What:   Technical-project report describing sample abundance calculations,
        wet-kg/m2 conventions, grades, and resource modeling in the TOML area.
Use:    Contractor-area maps, summary statistics, and methods.
Work:   Locate the authoritative report copy and attachments; digitize station
        maps only if the underlying table cannot be obtained.
# 
# TIER 4 - CONTRACTOR AND NATIONAL PROGRAM PAPERS WITH PRIMARY SAMPLE DATA

## BGR / GERMANY

[25] BGR Area E1 resource case study, Minerals (2021)
Status: [MASS] [DIGITIZE] [CONTACT]
Link:   https://www.mdpi.com/2075-163X/11/6/618
What:   Primary BGR exploration results from multiple expeditions, including
        box-core abundance measurements, resource statistics, and geostatistical
        maps for Area E1.
Use:    Modern BGR-area abundance ranges, sampling design, model methodology,
        and station-map digitization.
Work:   Search article supplements and cited cruise reports for the raw table;
        otherwise extract plotted sample locations and map values.

[26] BGR Environmental Impact Statement for harvester testing
Status: [MASS] [DIGITIZE] [CONTACT]
Link:   https://www.bgr.bund.de/EN/Themen/MarineRohstoffforschung/Downloads/2025_Manganknollen_241218_BGR_EIS.html
What:   Large BGR EIS covering the collector/harvester test area, baseline
        surveys, maps, sample locations, and local nodule/resource context.
Use:    Test-site geometry, station lists, survey methods, and possibly tabulated
        abundance or coverage.
Work:   Download the PDF, extract all appendices and tables, then georeference
        maps. Search for 'kg/m2', 'abundance', 'box corer', and station IDs.

[27] RWTH Aachen thesis - BGR E1 abundance and grade modeling
Status: [MASS] [GRADE] [DIGITIZE]
Link:   https://publications.rwth-aachen.de/record/761787/
What:   Thesis using 55 BGR E1 box-core samples with nodule abundance and Cu, Ni,
        and Co data; reports interpolated dry abundance around 10.29-21.31 kg/m2.
Use:    Potential 55-station abundance/grade table, geostatistical maps, and
        preprocessing methodology.
Work:   Search appendices and embedded tables; contact the author or BGR if the
        55-row input table is not included.

[28] Knobloch et al. - predictive mapping/resource estimation
Status: [MASS] [GRID] [DIGITIZE]
Link:   https://doi.org/10.1007/978-3-319-52557-0_6
What:   BGR-area predictive mapping using artificial neural networks and
        geostatistics.
Use:    Model covariates, validation targets, sample-density information, and
        abundance maps.
Work:   Trace every cited BGR input dataset and avoid treating predictions as
        observations.

[29] BGR CCZ exploration project hub
Status: [HUB]
Link:   https://www.bgr.bund.de/EN/Themen/MarineRohstoffforschung/Erkundung-mariner-mineralischer-Rohstoffe/erkundung-mariner-mineralischer-rohstoffe_node_en.html
What:   Official BGR exploration hub with project summaries, reports, contacts,
        and linked publications.
Use:    Locate expedition reports and identify the data custodian for a request
        for non-confidential box-core abundance tables.

[30] BGR MiningImpact expedition logbook
Status: [HUB]
Link:   https://www.bgr.bund.de/EN/Themen/MarineRohstoffforschung/MiningImpact-Logbuch/aktuelles_node_en.html
What:   Official expedition/logbook material for MANGAN2021 and the BGR/GSR
        collector trial.
Use:    Resolve cruise dates, station naming, instruments, and trial-site layout.

## IOM / INTEROCEANMETAL

[31] IOM - automated image-based abundance estimation, Minerals (2020)
Status: [MASS] [COVER] [DIGITIZE] [CONTACT]
Link:   https://www.mdpi.com/2075-163X/10/3/263
What:   Uses 63 physical box-core wet-abundance measurements, 63 co-located
        photographs, and 26,352 photographic abundance estimates in IOM block H22.
Use:    One of the best published bridges between image cover and measured wet
        kg/m2; ideal calibration data if the 63-row table can be recovered.
Work:   Extract figures/tables/supplements, then request the 63 paired records
        and image-derived estimates from IOM or the authors.

[32] IOM H22_NE nodule geochemistry, Minerals (2025)
Status: [MASS] [GRADE] [SUPP]
Link:   https://www.mdpi.com/2075-163X/15/2/154
What:   Thirteen box-core stations in IOM H22_NE, reported wet-abundance range
        of approximately 10.3-19.9 kg/m2, plus detailed chemistry of 17 nodules
        and supplementary analytical tables.
Use:    Recent station IDs, abundance range, coordinates/sampling design, and
        metal-grade observations.
Work:   Check Supplement S1 and tables for per-station abundance; otherwise use
        the paper to request the 13 station values.

[33] IOM geological survey of polymetallic nodules
Status: [MASS] [GRADE] [DIGITIZE] [CONTACT]
Access lead: https://www.researchgate.net/publication/397706266_Geological_survey_of_deep-sea_polymetallic_nodules_in_the_Interoceanmetal_exploration_area
What:   Primary overview of 21 pre-2001 cruises and later IOM campaigns using box
        coring, photography, abundance, and metal-grade surveys.
Use:    Roadmap to IOM technical reports from 2007, 2011, 2015, and 2020.
Work:   Mine the reference list for report titles and request open/non-confidential
        station appendices from IOM.

[34] IOM first-phase survey results, 2001-2016
Status: [MASS] [GRADE] [DIGITIZE] [CONTACT]
Access lead: https://www.researchgate.net/publication/353550649_Results_of_the_first_phase_of_the_deep-sea_polymetallic_nodules_geological_survey_in_the_Interoceanmetal_Joint_Organization_licence_area_2001-2016
What:   Summary of IOM geological exploration, resource blocks, sampling methods,
        and results from the first exploration phase.
Use:    Locate block-level abundance statistics and the underlying cruise/report
        series.
Work:   Extract maps and table references; request station data by report/cruise.

[35] IOM cobalt-abundance estimation study
Status: [MASS] [GRADE] [DIGITIZE] [CONTACT]
Access lead: https://www.researchgate.net/publication/281677383_Variability_and_indirect_method_of_cobalt_abundance_estimation_in_the_polymetallic_nodules_the_INTEROCEANMETAL_exploration_area_Pacific_Ocean
What:   Study based on approximately 500 stations with nodule mass/abundance and
        metal-content information.
Use:    Large primary sample population and metal-abundance modeling.
Work:   Determine whether tables are embedded; otherwise digitize maps and make
        a targeted request for the 500-station input matrix.

[36] IOM geostatistical resource estimation study
Status: [MASS] [GRADE] [DIGITIZE] [CONTACT]
Access lead: https://www.researchgate.net/publication/326693751_Estimating_the_resources_of_polymetallic_nodules_in_the_Pacific_on_the_basis_of_their_genetic_characteristics_and_geostatistical_methods_Clarion-Clipperton_Zone_The_Interoceanmetal_area
What:   Geostatistical analysis reported to use hundreds of IOM stations with
        abundance and metal content.
Use:    Sampling density, variograms, resource maps, and station-count evidence.
Work:   Treat maps as predictions; pursue the input station table separately.

[37] IOM publication directory
Status: [HUB]
Link:   https://iom.gov.pl/publications/
What:   Official IOM list of papers and reports, including geological surveys,
        pre-feasibility work, and image-based abundance studies.
Use:    Primary discovery page for older reports and future open attachments.

[38] IOM 2024 research cruise
Status: [HUB] [CONTACT]
Link:   https://iom.gov.pl/iom-2024-research-cruise/
What:   Official cruise summary documenting recent box-corer and ROV work in H22.
Use:    Identify new station data likely to appear in reports or publications.
Work:   Add cruise/report alerts and request non-confidential station metadata.

## KOREA / KIOST

[39] Lee and Kim (2004) - Korean CCZ abundance prediction
Status: [MASS] [COVER] [DIGITIZE] [CONTACT]
DOI:    https://doi.org/10.1080/10641190490473434
KIOST record: https://sciwatch.kiost.ac.kr/handle/2020.kiost/5313?mode=simple
What:   Primary Korean exploration study combining MR1 side-scan sonar with
        free-fall-grab nodule abundance observations.
Use:    Station samples, acoustic predictors, and contractor-area abundance maps.
Work:   Obtain the full article and supplements; digitize station/map values if
        the grab table is not published.

[40] KIOST/KODOS nodule formation and sediment study (1994)
Status: [MASS] [DIGITIZE]
Link:   https://sciwatch.kiost.ac.kr/handle/2020.kiost/6460?mode=full
What:   Korean Deep Ocean Study area research reporting patchy nodule pavements
        and abundance conditions above 5 kg/m2 with geological controls.
Use:    Early Korean station/area context and references to source cruises.
Work:   Extract maps, station list, and cited cruise reports.

## RUSSIAN / SOVIET PROGRAMS

[41] Local variations in CCZ nodule abundance and composition (1992)
Status: [MASS] [GRADE] [DIGITIZE]
Link:   https://www.sciencedirect.com/science/article/pii/002532279290028G
What:   Primary study from five Soviet expeditions between 1968 and 1988 across
        seven CCZ areas, with abundance and geochemical variation.
Use:    Older western/central CCZ observations not well represented in modern
        contractor publications.
Work:   Extract tables and georeference figures; trace expedition station lists.

[42] PANGAEA - Soviet/Russian CCZ nodule stations, Barash and Kruglikova
Status: [NOW] [GRADE] [HUB]
Link:   https://doi.org/10.1594/PANGAEA.727500
What:   Coordinates and metadata for 19 CCZ nodule stations from Soviet/Russian
        cruises.
Use:    Station crosswalk for age/geochemistry publications and digitized
        abundance maps.
Work:   Join by cruise/station and do not infer kg/m2 unless the source reports it.

## FRANCE / IFREMER / NODINAUT

[43] IOC Technical Series 69 - Eastern Equatorial Pacific nodule ecosystem
Status: [COVER] [COUNT] [DIGITIZE] [HUB]
Link:   https://www.jodc.go.jp/info/ioc_doc/Technical/149556e.pdf
What:   Major photographic/ecosystem synthesis tied to French NODINAUT and
        other eastern equatorial Pacific nodule work, with maps, station context,
        and descriptions of nodule fields.
Use:    Locate NODINAUT stations, imagery, and older French technical references.
Work:   Search the PDF for nodule abundance, coverage, station tables, and cited
        cruise reports; separate ecological organism abundance from nodule data.

[44] NODINAUT seafloor recovery study
Status: [COUNT] [COVER] [DIGITIZE]
Open PDF lead: https://citeseerx.ist.psu.edu/document?doi=412cad69fbfec95baf0e4f22b38a7f01ac2fc0f7&repid=rep1&type=pdf
What:   Primary observations from the 2004 NODINAUT cruise in the French CCZ
        license area, used to study recovery of disturbed nodule seafloor.
Use:    Site coordinates, disturbance tracks, visible nodule setting, and cited
        French baseline data.
Work:   Extract location and nodule metrics; follow references to the original
        IFREMER cruise data and reports.

## GSR / BELGIUM

[45] GSR collector-trial impact study, Frontiers (2024)
Status: [MASS] [COVER] [DIGITIZE]
Link:   https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2024.1380530/full
What:   Primary trial-site study reporting local wet nodule-abundance context
        around 20-24 kg/m2 and the collector-test sampling design.
Use:    Site geometry, abundance range, and links to MiningImpact datasets.
Work:   Follow every data-availability and supplementary link; connect with [14].

[46] GSRNOD17 sample-site study and De Smet abundance reference
Status: [MASS] [DIGITIZE] [CONTACT]
Link:   https://doi.org/10.1525/elementa.2025.000016
What:   Primary GSR-area study comparing sites with different measured nodule
        abundances and explicitly citing De Smet et al. (2017) for kg/m2 values.
Use:    Follow the De Smet reference and supplementary station metadata to the
        original B4S03/B6S02 abundance observations.
Work:   Treat this as a lead to the primary abundance table, not a substitute.
# 
# TIER 5 - METAL-GRADE DATASETS TO JOIN WITH ABUNDANCE STATIONS

[47] PANGAEA - digitized Scripps CCZ nodule chemistry
Status: [NOW] [GRADE]
Link:   https://doi.org/10.1594/PANGAEA.957326
What:   Station-level geochemistry digitized from Scripps cruises, with sample
        coordinates and historic CCZ coverage.
Use:    Join metal grades to abundance stations by cruise/event/coordinates.
Work:   Preserve analytical method and source publication; apply spatial/time
        tolerance only after exact station-ID matching fails.

[48] PANGAEA - MANOP nodule chemistry
Status: [NOW] [GRADE]
Link:   https://doi.org/10.1594/PANGAEA.961506
What:   Sample-level nodule chemistry from MANOP sites, including Site S within
        the CCZ, with coordinates and station metadata.
Use:    Grade observations and geochemical validation for historic abundance.

[49] PANGAEA - SO268 / collector-test nodule chemistry
Status: [NOW] [GRADE]
Link:   https://doi.org/10.1594/PANGAEA.960339
What:   Chemical composition of nodules associated with a full-scale collector
        vehicle test in the CCZ.
Use:    Join modern BGR/GSR test-site grades with [01], [05], [13], and [14].

[50] PANGAEA - international collector-system nodule/crust chemistry
Status: [NOW] [GRADE]
Link:   https://doi.org/10.1594/PANGAEA.961091
What:   CCZ nodule and crust chemistry associated with a full-scale collector
        system study, with sample metadata.
Use:    Additional modern grade observations and collector-site crosswalks.

[51] PANGAEA - DOMES Site A AAS chemistry
Status: [NOW] [GRADE]
Link:   https://doi.org/10.1594/PANGAEA.877894
What:   Box-core nodule chemistry measured by atomic absorption spectroscopy at
        DOMES Site A.
Use:    Exact/near-exact station joins to DOMES abundance datasets [02]-[04].

[52] PANGAEA - DOMES Site A NAA chemistry
Status: [NOW] [GRADE]
Link:   https://doi.org/10.1594/PANGAEA.877895
What:   Neutron activation analysis for DOMES Site A nodule samples.
Use:    Independent analytical-method grade data for the same historic station
        family; useful for cross-method quality control.

[53] NOAA/NCEI Marine Minerals Database
Status: [NOW] [GRADE] [HUB] [DUPLICATE]
Link:   https://www.ngdc.noaa.gov/mgg/geology/mmdb.html
What:   Official download hub for NOAA ferromanganese compilations, CNEXO data,
        Scripps nodule descriptions/analyses, and related marine-mineral files.
Use:    Bulk historic station coordinates, sample descriptions, chemistry, and
        bibliography.
Work:   Compare records with PANGAEA migrated versions before ingestion.

[54] NOAA/NCEI MMS marine-minerals CD-ROM documentation
Status: [NOW] [GRADE] [HUB]
Link:   https://www.ngdc.noaa.gov/mgg/fliers/92mgg05.html
What:   Describes ASCII, dBase, and spreadsheet files for historic marine-mineral
        datasets, including Scripps and CNEXO nodule compilations.
Use:    File-format guide and bulk-download provenance.

[55] Scripps Mn Nodule Analysis File metadata and download
Status: [NOW] [GRADE]
Link:   https://pubs.usgs.gov/of/2006/1195/data/metadata/NOAA/NGDC/MnNOD_meta.html
What:   Roughly 1,500 analyses from about 800 locations, with coordinates,
        depth, sampling device, nodule type, and chemistry.
Use:    Large historic grade table and station crosswalk.
Work:   Filter to CCZ bounds and look for station matches in [02], [03], [08],
        [21], and [22].

[56] NCEI - Scripps manganese-nodule descriptions
Status: [NOW] [GRADE] [HUB]
Link:   https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ngdc.mgg.geology%3AG00250
What:   Station/sample descriptions from cores, grabs, dredges, and box cores,
        primarily in the east-central Pacific.
Use:    Sampling-method metadata, qualitative nodule occurrence, and station IDs.

[57] CNEXO worldwide ferromanganese concretion compilation
Status: [NOW] [GRADE]
Link:   https://catalog.data.gov/dataset/cnexo-world-wide-compilation-of-published-multi-component-analyses-of-ferromanganese-concr
What:   Coordinates, depth, lithology, chemistry, and references for published
        ferromanganese nodule/concretion samples.
Use:    Filter to CCZ and connect French/CNEXO samples to NODINAUT-era sources.

[58] PANGAEA - Korean license-area sediment geochemistry
Status: [NOW] [GRADE]
Link:   https://doi.org/10.1594/PANGAEA.945266
What:   Station-level sediment geochemistry and coordinates in the Korean CCZ
        license area.
Use:    Environmental covariates for abundance prediction, not nodule abundance.

[59] PANGAEA - SO239 CCZ nodule radioisotopes and station crosswalk
Status: [NOW] [GRADE] [HUB]
Link:   https://doi.org/10.1594/PANGAEA.951145
What:   Box-core stations across BGR, IOM, GSR, IFREMER, and APEI-3 with nodule
        radioisotope measurements and coordinates.
Use:    Cross-contractor station vocabulary and location validation.

[60] PANGAEA - Valdivia 1974 CCZ expedition samples
Status: [NOW] [HUB]
Link:   https://doi.org/10.1594/PANGAEA.868735
What:   Annotated CCZ expedition sample descriptions and coordinates from the
        1974 Valdivia cruise.
Use:    Historical station discovery and qualitative nodule-occurrence context.
# 
# TIER 6 - SPATIAL REFERENCE AND SOURCE-DISCOVERY HUBS

[61] GSR official contract-area ArcGIS layer
Status: [NOW] [HUB]
Link:   https://services5.arcgis.com/VcAAb5oBhdAAnFj2/ArcGIS/rest/services/fclContractAreas_20240724/FeatureServer/10
What:   Machine-readable GSR contract-area geometry available through an ArcGIS
        FeatureServer.
Use:    Spatially tag all GSR observations and detect records outside the area.

[62] BGR marine mineral resources home
Status: [HUB]
Link:   https://www.bgr.bund.de/EN/Themen/MarineRohstoffforschung/marinerohstoffforschung_node_en.html
What:   Official BGR marine-resource archive and publication/contact gateway.
Use:    Find reports not indexed well by academic search engines.

[63] IOM history and program page
Status: [HUB]
Link:   https://iom.gov.pl/iom-story/
What:   Official IOM exploration history, area development, and project context.
Use:    Resolve former block names, cruise periods, and organizational contacts.
# 
# RECOMMENDED INGESTION ORDER

## PHASE A - ONE-DAY DOWNLOAD QUEUE
  1. [01] SO268 box-core summary
  2. [02] DOMES floor density
  3. [03] DOMES Piper abundance
  4. [04] DOMES Site C size/weight
  5. [05] SO268 individual nodules
  6. [06] Dryad chamber/nodule workbooks
  7. [11] Amon supplementary image table
  8. [12] APEI-6 PANGAEA cover data
  9. [14] GSR Mendeley data
 10. [18]-[19] regional ISA/Washburn grid data

## PHASE B - PDF AND SUPPLEMENT EXTRACTION
  1. [25]-[28] BGR papers, thesis, and EIS
  2. [31]-[36] IOM paired samples and large station populations
  3. [39]-[40] Korean/KIOST studies
  4. [41] Soviet expedition paper
  5. [43]-[44] IFREMER/NODINAUT material
  6. [23]-[24] commercial technical reports

## PHASE C - TARGETED DATA REQUESTS
Request only specific, clearly non-confidential tables:

  - BGR: the 55 E1 box-core abundance/grade inputs cited in the RWTH thesis,
    plus station IDs and wet/dry conversion metadata.
  - IOM: the 63 paired box-core/photo records used in the 2020 paper; the 13
    H22_NE station abundances from the 2025 paper; and the published-paper input
    matrices described as 448-500 stations.
  - KIOST: the free-fall-grab abundance table behind Lee and Kim (2004).
  - GSR/MiningImpact: observed kg/m2 values linked to B4S03/B6S02 and collector
    trial stations.
  - IFREMER: NODINAUT/BIONOD station-level nodule cover, count, or mass data that
    have already appeared in publications or public technical reports.
# 
# MASTER CATALOG SCHEMA

Each recovered observation should have at least:

  source_record_id
  source_title
  source_url
  source_doi
  source_type                 # dataset, paper, report, thesis, image
  source_accessed_date
  license
  cruise
  expedition_leg
  contractor_or_area
  station_id
  event_id
  sample_datetime_utc
  latitude
  longitude
  water_depth_m
  sample_method               # box core, grab, dredge, image, AUV, OFOS
  sampled_area_m2
  abundance_value_original
  abundance_unit_original
  abundance_basis             # wet, dry, unknown
  nodule_mass_kg
  abundance_kg_m2
  nodule_count
  nodule_density_m2
  visible_cover_percent
  buried_nodule_count
  mean_nodule_mass_g
  median_nodule_size_mm
  cu_percent
  ni_percent
  co_percent
  mn_percent
  fe_percent
  derivation_formula
  observation_or_prediction   # observed, compiled grid, interpolated, modelled
  quality_grade
  duplicate_group_id
  notes
# 
# CRITICAL DUPLICATE RULES

1. [02], [03], [04], [09], and [10] are overlapping DOMES publication families.
   Deduplicate by cruise + station/event + coordinates + sampling date, not DOI.

2. PANGAEA records migrated from NOAA/NCEI can duplicate [53]-[57]. Prefer the
   record with the clearest methods and fields, but retain both provenance links.

3. [18], [19], [20], [21], [22], and [23] may recycle the same historic source
   observations. Label them as compilations/grids until a raw station record is
   recovered.

4. Individual nodules in [05] are subsamples nested inside box-core events in
   [01]. The spatial sample is the event, not each nodule.

5. Image cover/count and recovered mass are different observation classes.
   Never silently convert percent cover to kg/m2. Store any empirical conversion
   model and its uncertainty separately.
# 
# BOTTOM LINE

Path C is viable. The open literature already provides several genuine numeric
station/event datasets, especially the PANGAEA SO268 and DOMES records. The
largest remaining prize is not another regional map; it is recovering the
published-but-not-attached input tables behind BGR, IOM, KIOST, GSR, and older
Soviet/IFREMER studies. Those tables should be pursued with precise requests,
while image cover and regional grids are ingested as separate evidence classes.