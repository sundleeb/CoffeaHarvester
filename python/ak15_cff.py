import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import *
from Configuration.Eras.Modifier_run2_miniAOD_80XLegacy_cff import run2_miniAOD_80XLegacy

# ---------------------------------------------------------


def setupAK15(process, runOnMC=False, path=None):
    # recluster Puppi jets
    bTagDiscriminators = [
        'pfJetProbabilityBJetTags',
        'pfCombinedInclusiveSecondaryVertexV2BJetTags',
    ]
    subjetBTagDiscriminators = [
        'pfJetProbabilityBJetTags',
        'pfCombinedInclusiveSecondaryVertexV2BJetTags',
    ]
    JETCorrLevels = ['L2Relative', 'L3Absolute', 'L2L3Residual']

    from PhysicsTools.NanoTuples.jetToolbox_cff import jetToolbox
    jetToolbox(process, 'ak15', 'dummySeqAK15', 'out', associateTask=False,
               PUMethod='Puppi', JETCorrPayload='AK8PFPuppi', JETCorrLevels=JETCorrLevels,
               Cut='pt > 160.0 && abs(rapidity()) < 2.4',
               miniAOD=True, runOnMC=runOnMC,
               addNsub=True, maxTau=3,
               addSoftDrop=True, addSoftDropSubjets=True, subJETCorrPayload='AK4PFPuppi', subJETCorrLevels=JETCorrLevels,
               bTagDiscriminators=bTagDiscriminators, subjetBTagDiscriminators=subjetBTagDiscriminators)

    if runOnMC:
        process.ak15GenJetsNoNu.jetPtMin = 100
        process.ak15GenJetsNoNuSoftDrop.jetPtMin = 100

    from PhysicsTools.PatAlgos.tools.jetTools import updateJetCollection
    from RecoBTag.MXNet.pfDeepBoostedJet_cff import _pfMassDecorrelatedDeepBoostedJetTagsProbs as pfMassDecorrelatedDeepBoostedJetTagsProbs

    updateJetCollection(
        process,
        jetSource=cms.InputTag('packedPatJetsAK15PFPuppiSoftDrop'),
        rParam=1.5,
        jetCorrections=('AK8PFPuppi', cms.vstring(['L2Relative', 'L3Absolute']), 'None'),
        btagDiscriminators=bTagDiscriminators + pfMassDecorrelatedDeepBoostedJetTagsProbs,
        postfix='AK15WithPuppiDaughters',
    )

    # configure DeepAK15
    from PhysicsTools.NanoTuples.pfDeepBoostedJetPreprocessParamsAK15_cfi import pfDeepBoostedJetPreprocessParams as params
    process.pfDeepBoostedJetTagInfosAK15WithPuppiDaughters.jet_radius = 1.5
    process.pfMassDecorrelatedDeepBoostedJetTagsAK15WithPuppiDaughters.preprocessParams = params
    process.pfMassDecorrelatedDeepBoostedJetTagsAK15WithPuppiDaughters.model_path = 'PhysicsTools/NanoTuples/data/DeepBoostedJet/ak15/decorrelated/resnet-symbol.json'
    process.pfMassDecorrelatedDeepBoostedJetTagsAK15WithPuppiDaughters.param_path = 'PhysicsTools/NanoTuples/data/DeepBoostedJet/ak15/decorrelated/resnet.params'

    # src
    srcJets = cms.InputTag('selectedUpdatedPatJetsAK15WithPuppiDaughters')

    # jetID
    process.looseJetIdAK15Puppi = cms.EDProducer("PatJetIDValueMapProducer",
        filterParams=cms.PSet(
            version=cms.string('WINTER16'),
            quality=cms.string('LOOSE'),
        ),
        src=srcJets
    )

    process.tightJetIdAK15Puppi = cms.EDProducer("PatJetIDValueMapProducer",
        filterParams=cms.PSet(
            version=cms.string('WINTER17'),
            quality=cms.string('TIGHT'),
        ),
        src=srcJets
    )
    run2_miniAOD_80XLegacy.toModify(process.tightJetIdAK15Puppi.filterParams, version="WINTER16")

    process.tightJetIdLepVetoAK15Puppi = cms.EDProducer("PatJetIDValueMapProducer",
        filterParams=cms.PSet(
            version=cms.string('WINTER17'),
            quality=cms.string('TIGHTLEPVETO'),
        ),
        src=srcJets
    )

    process.ak15WithUserData = cms.EDProducer("PATJetUserDataEmbedder",
        src=srcJets,
        userFloats=cms.PSet(),
        userInts=cms.PSet(
            tightId=cms.InputTag("tightJetIdAK15Puppi"),
            tightIdLepVeto=cms.InputTag("tightJetIdLepVetoAK15Puppi"),
        ),
    )
    run2_miniAOD_80XLegacy.toModify(process.ak15WithUserData.userInts,
        looseId=cms.InputTag("looseJetIdAK15Puppi"),
        tightIdLepVeto=None,
    )

    process.ak15Table = cms.EDProducer("SimpleCandidateFlatTableProducer",
        src=cms.InputTag("ak15WithUserData"),
        name=cms.string("AK15Puppi"),
        cut=cms.string(""),
        doc=cms.string("ak15 puppi jets"),
        singleton=cms.bool(False),  # the number of entries is variable
        extension=cms.bool(False),  # this is the main table for the jets
        variables=cms.PSet(P4Vars,
            jetId=Var("userInt('tightId')*2+4*userInt('tightIdLepVeto')", int, doc="Jet ID flags bit1 is loose (always false in 2017 since it does not exist), bit2 is tight, bit3 is tightLepVeto"),
            area=Var("jetArea()", float, doc="jet catchment area, for JECs", precision=10),
            rawFactor=Var("1.-jecFactor('Uncorrected')", float, doc="1 - Factor to get back to raw pT", precision=6),
            tau1=Var("userFloat('NjettinessAK15Puppi:tau1')", float, doc="Nsubjettiness (1 axis)", precision=10),
            tau2=Var("userFloat('NjettinessAK15Puppi:tau2')", float, doc="Nsubjettiness (2 axis)", precision=10),
            tau3=Var("userFloat('NjettinessAK15Puppi:tau3')", float, doc="Nsubjettiness (3 axis)", precision=10),
            msoftdrop=Var("groomedMass()", float, doc="Corrected soft drop mass with PUPPI", precision=10),
            btagCSVV2=Var("bDiscriminator('pfCombinedInclusiveSecondaryVertexV2BJetTags')", float, doc="pfCombinedInclusiveSecondaryVertexV2 b-tag discriminator (aka CSVV2)", precision=10),
            btagJP=Var("bDiscriminator('pfJetProbabilityBJetTags')", float, doc="pfJetProbabilityBJetTags b-tag discriminator (aka JP)", precision=10),
            nBHadrons=Var("jetFlavourInfo().getbHadrons().size()", int, doc="number of b-hadrons"),
            nCHadrons=Var("jetFlavourInfo().getcHadrons().size()", int, doc="number of c-hadrons"),
            subJetIdx1=Var("?nSubjetCollections()>0 && subjets().size()>0?subjets()[0].key():-1", int,
                 doc="index of first subjet"),
            subJetIdx2=Var("?nSubjetCollections()>0 && subjets().size()>1?subjets()[1].key():-1", int,
                 doc="index of second subjet"),
        )
    )
    run2_miniAOD_80XLegacy.toModify(process.ak15Table.variables, jetId=Var("userInt('tightId')*2+userInt('looseId')", int, doc="Jet ID flags bit1 is loose, bit2 is tight"))
    process.ak15Table.variables.pt.precision = 10

    # add Mass Decorrelated taggers
    for prob in pfMassDecorrelatedDeepBoostedJetTagsProbs:
        name = prob.split(':')[1]
        setattr(process.ak15Table.variables, name, Var("bDiscriminator('%s')" % prob, float, doc=prob, precision=-1))

    process.ak15SubJetTable = cms.EDProducer("SimpleCandidateFlatTableProducer",
        src=cms.InputTag("selectedPatJetsAK15PFPuppiSoftDropPacked", "SubJets"),
        cut=cms.string(""),
        name=cms.string("AK15PuppiSubJet"),
        doc=cms.string("ak15 puppi subjets"),
        singleton=cms.bool(False),  # the number of entries is variable
        extension=cms.bool(False),  # this is the main table for the jets
        variables=cms.PSet(P4Vars,
            area=Var("jetArea()", float, doc="jet catchment area, for JECs", precision=10),
            rawFactor=Var("1.-jecFactor('Uncorrected')", float, doc="1 - Factor to get back to raw pT", precision=6),
            btagCSVV2=Var("bDiscriminator('pfCombinedInclusiveSecondaryVertexV2BJetTags')", float, doc=" pfCombinedInclusiveSecondaryVertexV2 b-tag discriminator (aka CSVV2)", precision=10),
            btagJP=Var("bDiscriminator('pfJetProbabilityBJetTags')", float, doc="pfJetProbabilityBJetTags b-tag discriminator (aka JP)", precision=10),
            nBHadrons=Var("jetFlavourInfo().getbHadrons().size()", int, doc="number of b-hadrons"),
            nCHadrons=Var("jetFlavourInfo().getcHadrons().size()", int, doc="number of c-hadrons"),
        )
    )
    process.ak15SubJetTable.variables.pt.precision = 10

    process.ak15Task = cms.Task(
        process.tightJetIdAK15Puppi,
        process.tightJetIdLepVetoAK15Puppi,
        process.ak15WithUserData,
        process.ak15Table,
        process.ak15SubJetTable,
    )

    if runOnMC:
        process.genJetAK15Table = cms.EDProducer("SimpleCandidateFlatTableProducer",
            src=cms.InputTag("ak15GenJetsNoNu"),
            cut=cms.string("pt > 100."),
            name=cms.string("GenJetAK15"),
            doc=cms.string("AK15 GenJets made with visible genparticles"),
            singleton=cms.bool(False),  # the number of entries is variable
            extension=cms.bool(False),  # this is the main table for the genjets
            variables=cms.PSet(P4Vars,
            )
        )
        process.genJetAK15Table.variables.pt.precision = 10

        process.genSubJetAK15Table = cms.EDProducer("SimpleCandidateFlatTableProducer",
            src=cms.InputTag("ak15GenJetsNoNuSoftDrop", "SubJets"),
            cut=cms.string(""),
            name=cms.string("GenSubJetAK15"),
            doc=cms.string("AK15 Gen-SubJets made with visible genparticles"),
            singleton=cms.bool(False),  # the number of entries is variable
            extension=cms.bool(False),  # this is the main table for the genjets
            variables=cms.PSet(P4Vars,
            )
        )
        process.genSubJetAK15Table.variables.pt.precision = 10

        process.ak15Task.add(process.genJetAK15Table)
        process.ak15Task.add(process.genSubJetAK15Table)

    _ak15Task_80X = process.ak15Task.copy()
    _ak15Task_80X.replace(process.tightJetIdLepVetoAK15Puppi, process.looseJetIdAK15Puppi)
    run2_miniAOD_80XLegacy.toReplaceWith(process.ak15Task, _ak15Task_80X)

    if path is None:
        process.schedule.associate(process.ak15Task)
    else:
        getattr(process, path).associate(process.ak15Task)

# ---------------------------------------------------------
