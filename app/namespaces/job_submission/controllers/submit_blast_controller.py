"""
Module that describes and handles the requests concerned with the blast search submission
"""
from flask import request
from flask_restx import Namespace, Resource, fields

from app.namespaces.job_submission.services import job_submission_service
from app.namespaces.job_submission.shared_marshalls import BASE_SUBMISSION_RESPONSE
from app.namespaces.models import delayed_job_models

API = Namespace('submit/blast', description='Namespace to submit a BLAST job')

BLAST_JOB = API.model('BLASTJob', {
    'matrix': fields.String(description='(Protein searches) The substitution matrix used for scoring alignments when '
                                        'searching the database.', example='BLOSUM45',
                            enum=['BLOSUM45', 'BLOSUM50', 'BLOSUM62', 'BLOSUM80', 'BLOSUM90', 'PAM30', 'PAM70',
                                  'PAM250', 'NONE']),
    'alignments': fields.Integer(description='Maximum number of match alignments reported in the result output.',
                                 example=50, enum=[5, 10, 20, 50, 100, 150, 200, 500, 750, 1000], min=5, max=1000),
    'scores': fields.Integer(description='Maximum number of match score summaries reported in the result output.',
                             example=50, enum=[5, 10, 20, 50, 100, 150, 200, 500, 750, 1000], min=5, max=1000),
    'exp': fields.String(description='Limits the number of scores and alignments reported based on the expectation '
                                     'value. This is the maximum number of times the match is expected to occur by '
                                     'chance.', example='10', enum=['1e-200', '1e-100', '1e-50', '1e-10', '1e-5',
                                                                    '1e-4', '1e-3', '1e-2', '1e-1', '1.0', '10', '100',
                                                                    '1000']),
    'dropoff': fields.Integer(description='The amount a score can drop before gapped extension of word hits is halted',
                              example=0, min=0, max=10),
    'gapopen': fields.Integer(description='Penalty taken away from the score when a gap is created in sequence. '
                                          'Increasing the gap openning penalty will decrease the number of gaps in the '
                                          'final alignment.',
                              example=-1, min=-1, max=25),
    'gapext': fields.Integer(description='Penalty taken away from the score for each base or residue in the gap. '
                                         'Increasing the gap extension penalty favors short gaps in the final alignment'
                                         ', conversly decreasing the gap extension penalty favors long gaps in the '
                                         'final alignment.',
                             example=-1, min=-1, max=10),
    'filter': fields.String(description='Filter regions of low sequence complexity. This can avoid issues with low '
                                        'complexity sequences where matches are found due to composition rather than '
                                        'meaningful sequence similarity. However in some cases filtering also masks '
                                        'regions of interest and so should be used with caution.', example='F',
                            enum=['F', 'T']),
    'seqrange': fields.String(description='Specify a range or section of the input sequence to use in the search. '
                                          'Example: Specifying "34-89" in an input sequence of total length 100, will '
                                          'tell BLAST to only use residues 34 to 89, inclusive.',
                              example='START-END'),
    'gapalign': fields.String(description='Filter regions of low sequence complexity. This can avoid issues with low ',
                              example='true',
                              enum=['true', 'false']),
    'wordsize': fields.Integer(description='Word size for wordfinder algorithm',
                               example=6, min=6, max=28),
    'taxids': fields.String(description='Specify one or more TaxIDs so that the BLAST search becomes taxonomically '
                                        'aware.', example=''),
    'compstats': fields.String(description='se composition-based statistics.',
                               example='F', enum=['F', 'D', '1', '2', '3']),
    'align': fields.Integer(description='Formatting for the alignments',
                            example=0, min=0, max=12),
    'sequence': fields.String(description='The query sequence can be entered directly into this form. The sequence '
                                          'can be in GCG, FASTA, EMBL (Nucleotide only), GenBank, PIR, NBRF, PHYLIP '
                                          'or UniProtKB/Swiss-Prot (Protein only) format. A partially formatted '
                                          'sequence is not accepted. Adding a return to the end of the sequence may '
                                          'help certain applications understand the input. Note that directly using '
                                          'data from word processors may yield unpredictable results as hidden/control '
                                          'characters may be present.',
                              example='>sp|P35858|ALS_HUMAN Insulin-like growth factor-binding protein complex acid '
                                      'labile subunit OS=Homo sapiens GN=IGFALS PE=1 SV=1\n'
                                      'MALRKGGLALALLLLSWVALGPRSLEGADPGTPGEAEGPACPAACVCSYDDDADELSVFC\n'
                                      'SSRNLTRLPDGVPGGTQALWLDGNNLSSVPPAAFQNLSSLGFLNLQGGQLGSLEPQALLG\n'
                                      'LENLCHLHLERNQLRSLALGTFAHTPALASLGLSNNRLSRLEDGLFEGLGSLWDLNLGWN\n'
                                      'SLAVLPDAAFRGLGSLRELVLAGNRLAYLQPALFSGLAELRELDLSRNALRAIKANVFVQ\n'
                                      'LPRLQKLYLDRNLIAAVAPGAFLGLKALRWLDLSHNRVAGLLEDTFPGLLGLRVLRLSHN\n'
                                      'AIASLRPRTFKDLHFLEELQLGHNRIRQLAERSFEGLGQLEVLTLDHNQLQEVKAGAFLG\n'
                                      'LTNVAVMNLSGNCLRNLPEQVFRGLGKLHSLHLEGSCLGRIRPHTFTGLSGLRRLFLKDN\n'
                                      'GLVGIEEQSLWGLAELLELDLTSNQLTHLPHRLFQGLGKLEYLLLSRNRLAELPADALGP\n'
                                      'LQRAFWLDVSHNRLEALPNSLLAPLGRLRYLSLRNNSLRTFTPQPPGLERLWLEGNPWDC\n'
                                      'GCPLKALRDFALQNPSAVPRFVQAICEGDDCQPPAYTYNNITCASPPEVVGLDLRDLSEA\n'
                                      'HFAPC'),
})

SUBMISSION_RESPONSE = API.inherit('SubmissionResponse', BASE_SUBMISSION_RESPONSE)


@API.route('/')
class SubmitBLASTJob(Resource):
    """
        Resource that handles BLAST search job submission requests
    """
    job_type = delayed_job_models.JobTypes.BLAST

    @API.expect(BLAST_JOB)
    @API.doc(body=BLAST_JOB)
    @API.marshal_with(BASE_SUBMISSION_RESPONSE)
    def post(self):  # pylint: disable=no-self-use
        """
        Submits a job to the queue.
        :return: a json response with the result of the submission
        """

        json_data = request.json
        job_params = {
            **json_data,
            'search_type': str(self.job_type),
        }
        response = job_submission_service.submit_job(self.job_type, job_params)
        return response
