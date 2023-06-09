import os
#import IPython.display as ipd
import torch
#from torch.utils.data import DataLoader
from scipy.io.wavfile import write
from datetime import datetime

from .vits.Commons import intersperse
from .vits.Utils import get_hparams_from_file, load_checkpoint
#from .vits.Data_Utils import TextAudioSpeakerLoader, TextAudioSpeakerCollate
from .vits.Models import SynthesizerTrn
from .vits.text import text_to_sequence
from .vits.text.symbols import symbols


class Voice_Converting:
    '''
    Convert text to speech and save as audio files
    '''
    def __init__(self,
        Config_Path_Load: str = ...,
        Model_Path_Load: str = ...,
        Text: str = '请输入语句',
        Language: str = '[ZH]',
        Speaker: str = ...,
        EmotionStrength: float = .667,
        PhonemeDuration: float = 0.8,
        SpeechRate: float = 1.,
        Audio_Dir_Save: str = ...
    ):
        self.Config_Path_Load = Config_Path_Load
        self.Model_Path_Load = Model_Path_Load
        self.Text = Text
        self.Language = Language
        self.Speaker = Speaker
        self.EmotionStrength = EmotionStrength
        self.PhonemeDuration = PhonemeDuration
        self.SpeechRate = SpeechRate
        self.Audio_Dir_Save = Audio_Dir_Save

    def Converting(self):
        hps = get_hparams_from_file(self.Config_Path_Load)

        net_g = SynthesizerTrn(
            len(symbols),
            hps.data.filter_length // 2 + 1,
            hps.train.segment_size // hps.data.hop_length,
            n_speakers=hps.data.n_speakers,
            **hps.model).cuda()
        _ = net_g.eval()

        _ = load_checkpoint(self.Model_Path_Load, net_g, None)

        def get_text(text, hps):
            text_norm = text_to_sequence(text, hps.data.text_cleaners)
            if hps.data.add_blank:
                text_norm = intersperse(text_norm, 0)
            text_norm = torch.LongTensor(text_norm)
            return text_norm

        stn_tst = get_text((f"[{self.Language}]{self.Text}[{self.Language}]"), hps)
        with torch.no_grad():
            x_tst = stn_tst.cuda().unsqueeze(0)
            x_tst_lengths = torch.LongTensor([stn_tst.size(0)]).cuda()
            sid = torch.LongTensor([hps.speakers.index(self.Speaker)]).cuda()
            audio = net_g.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=self.EmotionStrength, noise_scale_w=self.PhonemeDuration, length_scale=self.SpeechRate)[0][0,0].data.cpu().float().numpy()
            write(os.path.normpath(f"{self.Audio_Dir_Save}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav"), hps.data.sampling_rate, audio) #ipd.display(ipd.Audio(audio, rate=hps.data.sampling_rate, normalize=False))


''' # Voice Conversion 
dataset = TextAudioSpeakerLoader(hps.data.validation_files, hps.data)
collate_fn = TextAudioSpeakerCollate()
loader = DataLoader(dataset, num_workers=8, shuffle=False,
    batch_size=1, pin_memory=True,
    drop_last=True, collate_fn=collate_fn)
data_list = list(loader)

with torch.no_grad():
    x, x_lengths, spec, spec_lengths, y, y_lengths, sid_src = [x.cuda() for x in data_list[0]]
    sid_tgt1 = torch.LongTensor([1]).cuda()
    sid_tgt2 = torch.LongTensor([2]).cuda()
    sid_tgt3 = torch.LongTensor([4]).cuda()
    audio1 = net_g.voice_conversion(spec, spec_lengths, sid_src=sid_src, sid_tgt=sid_tgt1)[0][0,0].data.cpu().float().numpy()
    audio2 = net_g.voice_conversion(spec, spec_lengths, sid_src=sid_src, sid_tgt=sid_tgt2)[0][0,0].data.cpu().float().numpy()
    audio3 = net_g.voice_conversion(spec, spec_lengths, sid_src=sid_src, sid_tgt=sid_tgt3)[0][0,0].data.cpu().float().numpy()
print("Original SID: %d" % sid_src.item())
ipd.display(ipd.Audio(y[0].cpu().numpy(), rate=hps.data.sampling_rate, normalize=False))
print("Converted SID: %d" % sid_tgt1.item())
ipd.display(ipd.Audio(audio1, rate=hps.data.sampling_rate, normalize=False))
print("Converted SID: %d" % sid_tgt2.item())
ipd.display(ipd.Audio(audio2, rate=hps.data.sampling_rate, normalize=False))
print("Converted SID: %d" % sid_tgt3.item())
ipd.display(ipd.Audio(audio3, rate=hps.data.sampling_rate, normalize=False))
'''