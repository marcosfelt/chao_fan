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
        mock_model.encode.return_value = "mocked_embeddings"
        sentences = ["This is a test.", "Another test sentence."]
        embeddings = generate_embeddings(sentences, mock_model)
        mock_model.encode.assert_called_once_with(sentences)
        self.assertEqual(embeddings, "mocked_embeddings")

if __name__ == '__main__':
    unittest.main()
