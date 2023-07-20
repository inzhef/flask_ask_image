from PIL import Image
from transformers import BlipProcessor, BlipForQuestionAnswering
import torch

processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")
model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base")

class BLIP_VQA:
    """Custom implementation of the BLIP model."""

    def __init__(self, vision_model, text_encoder, text_decoder, processor):
        """Initialize various objects"""
        self.vision_model = vision_model
        self.text_encoder = text_encoder
        self.text_decoder = text_decoder
        self.processor = processor

    def preprocess(self, img, ques):
        """preprocess the inputs: image, question"""
        inputs = self.processor(img, ques, return_tensors='pt')
        # store the pixel values of the image, input IDs (i.e., token IDs) of the question and the attention masks separately
        pixel_values = inputs['pixel_values']
        input_ids = inputs['input_ids']
        attention_mask = inputs['attention_mask']

        return pixel_values, input_ids, attention_mask


    def generate_output(self, pixel_values, input_ids, attention_mask):
        """Generates output from the preprocessed input"""

        # get the vision outputs (i.e., the image embeds)
        vision_outputs = self.vision_model(pixel_values=pixel_values)
        img_embeds = vision_outputs[0]

        # create attention mask with 1s on all the image embedding positions
        img_attention_mask = torch.ones(img_embeds.size()[: -1], dtype=torch.long)

        # encode the questions
        question_outputs = self.text_encoder(input_ids=input_ids,
                                             attention_mask=attention_mask,
                                             encoder_hidden_states=img_embeds,
                                             encoder_attention_mask=img_attention_mask,
                                             return_dict=False)

        # create attention mask with 1s on all the question token IDs positions
        question_embeds = question_outputs[0]
        question_attention_mask = torch.ones(question_embeds.size()[:-1], dtype=torch.long)

        # initialize the answers with the beginning-of-sentence IDs (bos ID)
        bos_ids = torch.full((question_embeds.size(0), 1), fill_value=30522)

        # get output from the decoder. These outputs are the generated IDs
        outputs = self.text_decoder.generate(
            input_ids=bos_ids,
            eos_token_id=102,
            pad_token_id=0,
            encoder_hidden_states=question_embeds,
            encoder_attention_mask=question_attention_mask)

        return outputs


    def postprocess(self, outputs):
        """post-process the output generated by the text-decoder"""

        return self.processor.decode(outputs[0], skip_special_tokens=True)


    def get_answer(self, image, ques):
        """Returns human friendly answer to a question"""

        # preprocess
        pixel_values, input_ids, attention_mask = self.preprocess(image, ques)
        # generate output
        outputs = self.generate_output(pixel_values, input_ids, attention_mask)
        # post-process
        answer = self.postprocess(outputs)
        return answer


