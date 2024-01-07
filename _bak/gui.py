import wx
import os
import sys
import logging
import _bak.audio_processing as ap
import certifi

# Set the path to cacert.pem
os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(certifi.where())

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.WARNING)

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, title="Tokoroten_ver0")
        self.SetTopWindow(self.frame)
        self.frame.Show()

        # Correctly indented: Configure logger to use the custom handler after frame is initialized
        log_handler = TextCtrlHandler(self.frame.log_text_ctrl)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(log_handler)

        return True


class MyFrame(wx.Frame):
    def __init__(self, parent, id=wx.ID_ANY, title="", 
                 pos=wx.DefaultPosition, size=wx.DefaultSize, 
                 style=wx.DEFAULT_FRAME_STYLE,
                 name="myframe"):
        super(MyFrame, self).__init__(parent, id, title, 
                                      pos, size, style, name)
        
        # Load size and position from config
        self.config = wx.Config('myapp')
        self.SetSize((self.config.ReadInt('width', 700), self.config.ReadInt('height', 500)))
        self.SetPosition((self.config.ReadInt('x', 50), self.config.ReadInt('y', 50)))
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Panel
        self.panel = wx.Panel(self)

        # Input Dir
        self.input_label = wx.StaticText(self.panel, label="Input Directory:")
        self.input_dir = wx.DirPickerCtrl(self.panel)
        self.input_dir.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnDirChanged)

        # Output Dir
        self.output_label = wx.StaticText(self.panel, label="Output Directory:")
        self.output_dir = wx.DirPickerCtrl(self.panel)
        self.output_dir.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnDirChanged)

        # Sources
        self.sources_label = wx.StaticText(self.panel, label="Sources:")
        self.vocals_check = wx.CheckBox(self.panel, label="vocals")
        self.drums_check = wx.CheckBox(self.panel, label="drums")
        self.bass_check = wx.CheckBox(self.panel, label="bass")
        self.other_check = wx.CheckBox(self.panel, label="other")

        # Status
        self.status_label = wx.StaticText(self.panel, label="Status:")
        self.status = wx.StaticText(self.panel, label="Idle")

        # Buttons
        self.run_button = wx.Button(self.panel, label="Run")
        self.run_button.Bind(wx.EVT_BUTTON, self.OnRun)
        self.exit_button = wx.Button(self.panel, label="Exit")
        self.exit_button.Bind(wx.EVT_BUTTON, self.OnExit)

        # Sizers
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.input_label, 0, wx.ALL, 5)
        self.main_sizer.Add(self.input_dir, 1, wx.ALL|wx.EXPAND, 5)
        self.main_sizer.Add(self.output_label, 0, wx.ALL, 5)
        self.main_sizer.Add(self.output_dir, 1, wx.ALL|wx.EXPAND, 5)
        self.main_sizer.Add(self.sources_label, 0, wx.ALL, 5)
        self.main_sizer.Add(self.vocals_check, 0, wx.ALL, 5)
        self.main_sizer.Add(self.drums_check, 0, wx.ALL, 5)
        self.main_sizer.Add(self.bass_check, 0, wx.ALL, 5)
        self.main_sizer.Add(self.other_check, 0, wx.ALL, 5)
        self.main_sizer.Add(self.status_label, 0, wx.ALL, 5)
        self.main_sizer.Add(self.status, 1, wx.ALL|wx.EXPAND, 5)
        self.main_sizer.Add(self.run_button, 0, wx.ALL|wx.CENTER, 5)
        self.main_sizer.Add(self.exit_button, 0, wx.ALL|wx.CENTER, 5)

        # Click Track Sample Picker
        self.click_sample_label = wx.StaticText(self.panel, label="Click Track Sample:")
        self.click_sample_path = wx.TextCtrl(self.panel, style=wx.TE_READONLY)
        self.click_sample_button = wx.Button(self.panel, label="Choose Click Sample")
        self.click_sample_button.Bind(wx.EVT_BUTTON, self.OnChooseClickSample)

        # Adding to Sizer
        self.main_sizer.Add(self.click_sample_label, 0, wx.ALL, 5)
        self.main_sizer.Add(self.click_sample_path, 1, wx.ALL|wx.EXPAND, 5)
        self.main_sizer.Add(self.click_sample_button, 0, wx.ALL|wx.CENTER, 5)


        self.panel.SetSizer(self.main_sizer)

        # Log Text Control
        self.log_text_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.main_sizer.Add(self.log_text_ctrl, 1, wx.ALL|wx.EXPAND, 5)
       
    def OnChooseClickSample(self, event):
        with wx.FileDialog(self, "Choose click sample", wildcard="WAV files (*.wav)|*.wav",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # ユーザーがキャンセルした場合
            # 選択されたファイルパスを保存
            self.click_sample_path.SetValue(fileDialog.GetPath())


    def OnDirChanged(self, event):
        logging.info(f"Directory changed: {event.GetPath()}")
        event.Skip()

    def OnRun(self, event):
        logging.info("Run button clicked")
        input_dir = self.input_dir.GetPath()
        output_dir = self.output_dir.GetPath()

        sources = []
        if self.vocals_check.GetValue():
            sources.append('vocals')
        if self.drums_check.GetValue():
            sources.append('drums')
        if self.bass_check.GetValue():
            sources.append('bass')
        if self.other_check.GetValue():
            sources.append('other')

        self.status.SetLabel("Running...")
        wx.Yield()  # Yield control to allow the GUI to update the status label

        for file_name in os.listdir(input_dir):
            logging.info(f"Processing {file_name}")
            if file_name.lower().endswith(('.wav', 'mp3')):
                file_path = os.path.join(input_dir, file_name)
                # クリックトラックのサンプルパスを取得
                click_sample_path = self.click_sample_path.GetValue()
                # 処理関数を呼び出し
                ap.process_audio_file_with_click_track(file_path, sources, 'umxl', 'cpu', output_dir, click_sample_path)

        self.status.SetLabel("Completed!")


    def OnClose(self, event):
        # Save size and position to config
        size = self.GetSize()
        pos = self.GetPosition()
        self.config.WriteInt('width', size.width)
        self.config.WriteInt('height', size.height)
        self.config.WriteInt('x', pos.x)
        self.config.WriteInt('y', pos.y)
        event.Skip()  # Skip the event to allow default handlers to process it (this will close the frame)

    def OnExit(self, event):
        logging.info("Exit button clicked")
        self.Close()

class TextCtrlHandler(logging.Handler):
    def __init__(self, text_ctrl):
        super().__init__()
        self.text_ctrl = text_ctrl

    def emit(self, record):
        msg = self.format(record)
        wx.CallAfter(self.text_ctrl.AppendText, msg + '\n')


if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
