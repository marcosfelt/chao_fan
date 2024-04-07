import unittest
from unittest.mock import MagicMock, patch

from chao_fan.integrations.sentence_transformer import (generate_embeddings,
                                                        get_model)


class TestSentenceTransformer(unittest.TestCase):
    @patch('chao_fan.integrations.sentence_transformer.SentenceTransformer')
    def test_get_model(self, mock_sentence_transformer):
        model = get_model()
        self.assertIsInstance(model, mock_sentence_transformer)

    @patch('chao_fan.integrations.sentence_transformer.SentenceTransformer')
    def test_generate_embeddings(self, mock_sentence_transformer):
        mock_model = MagicMock()
        mock_sentence_transformer.return_value = mock_model
        import numpy as np
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.5, 0.6, 0.7]])
        sentences = ["This is a test.", "Another test sentence."]
        embeddings = generate_embeddings(sentences, mock_model)
        mock_model.encode.assert_called_once_with(sentences)
        self.assertTrue((embeddings == np.array([[0.1, 0.2, 0.3], [0.5, 0.6, 0.7]])).all())

if __name__ == '__main__':
    unittest.main()
