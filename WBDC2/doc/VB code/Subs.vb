Imports System.Threading.Thread
Imports LabJack.LabJackUD
Module Subs
    Sub Initialize()
        ' IV Monitor scale factors
        P6VDScale = 4.0211
        P6VAScale = 4.0278
        N16VScale = 10.5446
        P16VScale = 10.5542
        P12VScale = 10.5827
        DCCurrent = 1
        IOffset = 0.026
        ThermOffset = -0.2389275
        ThermScale = 23.549488
        VCurrent = 0
        DetScale = 2.0064
        DetOffset = 0.004
        'Time and Data
        KBMain.TimeA.Text = System.DateTime.Now.Millisecond
        KBMain.DateA.Text = System.DateTime.Now.Date
        filenum = FreeFile()
        filenum1 = filenum + 1
        filenum2 = filenum + 2
        filenum3 = filenum + 3
        z = 1
        z1 = 1
        z3 = 1
        Initial_Gray()
    End Sub
    Sub GetIVMon()
        If i = 1 Then
            'CH0=+6VDCurrent    CH1=+6VDVolts    Latch1
            LATCHNUM = 0
            LATCHDATA = 0 + 0
            ProgLatch()

            'CH2=Det1     CH3=TEMP1     Latch2
            LATCHNUM = 1
            LATCHDATA = 0 + 0
            ProgLatch()

            'Get Data
            Read_Analog()
            KBMain.txtP6VDCurrent.Text = Format((ANALOG0 - IOffset) * DCCurrent, "0.000")
            KBMain.txtP6VDCurrent.BackColor = Color.White
            KBMain.txtP6VDVolts.Text = Format(ANALOG1 * P6VDScale, "0.000")
            KBMain.txtP6VDVolts.BackColor = Color.White
            KBMain.txtP12VVolts.BackColor = Color.LightGray
            KBMain.txtTEMP1.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP1.BackColor = Color.White
            KBMain.txtTEMP3.BackColor = Color.LightGray
            KBMain.txtDET1.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET1.BackColor = Color.White
            KBMain.txtDET4.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, z)
                Print(filenum, "  ")
                KBMain.TimeA.Text = System.DateTime.Now.Millisecond
                Print(filenum, KBMain.TimeA.Text)
                Print(filenum, "  ")
                Print(filenum, KBMain.txtP6VDVolts.Text)
                Print(filenum, "  ")
                Print(filenum, KBMain.txtP6VDCurrent.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, z)
                Print(filenum3, "  ")
                KBMain.TimeA.Text = System.DateTime.Now.Millisecond
                Print(filenum3, KBMain.TimeA.Text)
                Print(filenum3, "  ")
                Print(filenum3, KBMain.txtTEMP1.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, z)
                Print(filenum1, "  ")
                KBMain.TimeA.Text = System.DateTime.Now.Millisecond
                Print(filenum1, KBMain.TimeA.Text)
                Print(filenum1, "  ")
                Print(filenum1, KBMain.txtDET1.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 2 Then
            'CH0=+6VACurrent    CH1=+6VAVolts    Latch1
            LATCHNUM = 0
            LATCHDATA = 64 + 1
            ProgLatch()

            'CH2=Det2     CH3=TEMP2     Latch2
            LATCHNUM = 1
            LATCHDATA = 64 + 1
            ProgLatch()

            'Get Data
            Read_Analog()
            KBMain.txtP6VACurrent.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtP6VACurrent.BackColor = Color.White
            KBMain.txtP6VDCurrent.BackColor = Color.LightGray
            KBMain.txtP6VAVolts.Text = Format(ANALOG1 * P6VAScale, "0.000")
            KBMain.txtP6VAVolts.BackColor = Color.White
            KBMain.txtP6VDVolts.BackColor = Color.LightGray
            KBMain.txtTEMP2.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP2.BackColor = Color.White
            KBMain.txtTEMP1.BackColor = Color.LightGray
            KBMain.txtDET2.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET2.BackColor = Color.White
            KBMain.txtDET1.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtP6VAVolts.Text)
                Print(filenum, "  ")
                Print(filenum, KBMain.txtP6VACurrent.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP2.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET2.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 3 Then
            'CH0=+6VAFE1Current    CH1=+6VAVolts    Latch1
            LATCHNUM = 0
            LATCHDATA = 72 + 1
            ProgLatch()

            'CH2=Det3     CH3=TEMP3     Latch2
            LATCHNUM = 1
            LATCHDATA = 32 + 2
            ProgLatch()

            'Get Data
            Read_Analog()
            KBMain.txtP6VAFE1Current.Text = Format((ANALOG0 - IOffset) * DCCurrent, "0.000")
            KBMain.txtP6VAFE1Current.BackColor = Color.White
            KBMain.txtP6VACurrent.BackColor = Color.LightGray
            KBMain.txtTEMP3.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP3.BackColor = Color.White
            KBMain.txtTEMP2.BackColor = Color.LightGray
            KBMain.txtDET3.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET3.BackColor = Color.White
            KBMain.txtDET2.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtP6VAFE1Current.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP3.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET3.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 4 Then
            'CH0=+6VAFE2Current    CH1=+6VAVolts    Latch1
            LATCHNUM = 0
            LATCHDATA = 40 + 1
            ProgLatch()

            'CH2=Det4     CH3=TEMP1     Latch2
            LATCHNUM = 1
            LATCHDATA = 96 + 0
            ProgLatch()

            'Get Data
            Read_Analog()
            KBMain.txtP6VAFE2Current.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtP6VAFE2Current.BackColor = Color.White
            KBMain.txtP6VAFE1Current.BackColor = Color.LightGray
            KBMain.txtTEMP1.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP1.BackColor = Color.White
            KBMain.txtTEMP3.BackColor = Color.LightGray
            KBMain.txtDET4.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET4.BackColor = Color.White
            KBMain.txtDET3.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtP6VAFE2Current.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP1.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET4.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 5 Then
            'CH0=+16VFE1Current    CH1=+16VVolts    Latch1
            LATCHNUM = 0
            LATCHDATA = 96 + 2
            ProgLatch()

            'CH2=Det1     CH3=TEMP2     Latch2
            LATCHNUM = 1
            LATCHDATA = 0 + 1
            ProgLatch()

            'Get Data
            Read_Analog()
            VCurrent = ANALOG0 - IOffset
            KBMain.txtP16VFE1Current.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtP16VFE1Current.BackColor = Color.White
            KBMain.txtP6VAFE2Current.BackColor = Color.LightGray
            KBMain.txtP16VVolts.Text = Format(ANALOG1 * P16VScale, "0.000")
            KBMain.txtP16VVolts.BackColor = Color.White
            KBMain.txtP6VAVolts.BackColor = Color.LightGray
            KBMain.txtTEMP2.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP2.BackColor = Color.White
            KBMain.txtTEMP1.BackColor = Color.LightGray
            KBMain.txtDET1.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET1.BackColor = Color.White
            KBMain.txtDET4.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtP16VVolts.Text)
                Print(filenum, "  ")
                Print(filenum, KBMain.txtP16VFE1Current.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP2.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET1.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 6 Then
            'CH0=+16VFE2Current    CH1= +16VVolts   Latch1
            LATCHNUM = 0
            LATCHDATA = 16 + 2
            ProgLatch()

            'CH2=Det2     CH3=TEMP3     Latch2
            LATCHNUM = 1
            LATCHDATA = 64 + 2
            ProgLatch()

            'Get Data
            Read_Analog()
            VCurrent = ANALOG0 - IOffset + VCurrent
            KBMain.txtP16VFE2Current.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtP16VFE2Current.BackColor = Color.White
            KBMain.txtP16VFE1Current.BackColor = Color.LightGray
            KBMain.txtTEMP3.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP3.BackColor = Color.White
            KBMain.txtTEMP2.BackColor = Color.LightGray
            KBMain.txtDET2.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET2.BackColor = Color.White
            KBMain.txtDET1.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtP16VFE2Current.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP3.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET2.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 7 Then
            'CH0=+16VBE1Current    CH1= +16VVolts   Latch1
            LATCHNUM = 0
            LATCHDATA = 80 + 2
            ProgLatch()

            'CH2=Det3     CH3=TEMP1     Latch2
            LATCHNUM = 1
            LATCHDATA = 32 + 0
            ProgLatch()

            'Get Data
            Read_Analog()
            VCurrent = ANALOG0 - IOffset + VCurrent
            KBMain.txtP16VBE1Current.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtP16VBE1Current.BackColor = Color.White
            KBMain.txtP16VFE2Current.BackColor = Color.LightGray
            KBMain.txtTEMP1.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP1.BackColor = Color.White
            KBMain.txtTEMP3.BackColor = Color.LightGray
            KBMain.txtDET3.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET3.BackColor = Color.White
            KBMain.txtDET2.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtP16VBE1Current.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP1.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET3.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 8 Then
            'CH0=+16VBE2Current    CH1= +16VVolts   Latch1
            LATCHNUM = 0
            LATCHDATA = 48 + 2
            ProgLatch()

            'CH2=Det4     CH3=TEMP2     Latch2
            LATCHNUM = 1
            LATCHDATA = 96 + 1
            ProgLatch()

            'Get Data
            Read_Analog()
            VCurrent = ANALOG0 - IOffset + VCurrent
            KBMain.txtP16VBE2Current.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtP16VBE2Current.BackColor = Color.White
            KBMain.txtP16VBE1Current.BackColor = Color.LightGray
            KBMain.txtTEMP2.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP2.BackColor = Color.White
            KBMain.txtTEMP1.BackColor = Color.LightGray
            KBMain.txtDET4.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET4.BackColor = Color.White
            KBMain.txtDET3.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtP16VBE2Current.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP2.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET4.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 9 Then
            'CH0=+16VLOCurrent    CH1= +16VVolts   Latch1
            LATCHNUM = 0
            LATCHDATA = 112 + 2
            ProgLatch()

            'CH2=Det1     CH3=TEMP3     Latch2
            LATCHNUM = 1
            LATCHDATA = 0 + 2
            ProgLatch()

            'Get Data
            Read_Analog()
            VCurrent = ANALOG0 - IOffset + VCurrent
            KBMain.txtP16VLOCurrent.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtP16VLOCurrent.BackColor = Color.White
            KBMain.txtP16VBE2Current.BackColor = Color.LightGray
            KBMain.txtTEMP3.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP3.BackColor = Color.White
            KBMain.txtTEMP2.BackColor = Color.LightGray
            KBMain.txtDET1.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET1.BackColor = Color.White
            KBMain.txtDET4.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtP16VLOCurrent.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP3.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET1.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 10 Then
            'CH0=+16VD1Current    CH1= +16VVolts   Latch1
            LATCHNUM = 0
            LATCHDATA = 8 + 2
            ProgLatch()

            'CH2=Det2     CH3=TEMP1     Latch2
            LATCHNUM = 1
            LATCHDATA = 64 + 0
            ProgLatch()

            'Get Data
            Read_Analog()
            VCurrent = ANALOG0 - IOffset + VCurrent
            KBMain.txtP16ITotal.Text = Format(VCurrent, "0.000")
            KBMain.txtP16ITotal.BackColor = Color.White
            VCurrent = 0
            KBMain.txtP16VD1Current.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtP16VD1Current.BackColor = Color.White
            KBMain.txtP16VLOCurrent.BackColor = Color.LightGray
            KBMain.txtTEMP1.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP1.BackColor = Color.White
            KBMain.txtTEMP3.BackColor = Color.LightGray
            KBMain.txtDET2.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET2.BackColor = Color.White
            KBMain.txtDET1.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtP16VD1Current.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP1.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET2.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 11 Then
            'CH0=-16VCurrent    CH1= -16VVolts   Latch1
            LATCHNUM = 0
            LATCHDATA = 32 + 4
            ProgLatch()

            'CH2=Det3     CH3=TEMP2     Latch2
            LATCHNUM = 1
            LATCHDATA = 32 + 1
            ProgLatch()

            'Get Data
            Read_Analog()
            KBMain.txtN16VCurrent.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtN16VCurrent.BackColor = Color.White
            KBMain.txtP16VD1Current.BackColor = Color.LightGray
            KBMain.txtP16ITotal.BackColor = Color.LightGray
            KBMain.txtN16VVolts.Text = Format(-1 * (ANALOG1 * N16VScale), "0.000")
            KBMain.txtN16VVolts.BackColor = Color.White
            KBMain.txtP16VVolts.BackColor = Color.LightGray
            KBMain.txtTEMP2.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP2.BackColor = Color.White
            KBMain.txtTEMP1.BackColor = Color.LightGray
            KBMain.txtDET3.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET3.BackColor = Color.White
            KBMain.txtDET2.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtN16VVolts.Text)
                Print(filenum, "  ")
                Print(filenum, KBMain.txtN16VCurrent.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP2.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET3.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 12 Then
            'CH0=-16VFE1Current    CH1= -16VVolts   Latch1
            LATCHNUM = 0
            LATCHDATA = 104 + 4
            ProgLatch()

            'CH2=Det4     CH3=TEMP3     Latch2
            LATCHNUM = 1
            LATCHDATA = 96 + 2
            ProgLatch()

            'Get Data
            Read_Analog()
            KBMain.txtN16VFE1Current.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtN16VFE1Current.BackColor = Color.White
            KBMain.txtN16VCurrent.BackColor = Color.LightGray
            KBMain.txtTEMP3.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP3.BackColor = Color.White
            KBMain.txtTEMP2.BackColor = Color.LightGray
            KBMain.txtDET4.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET4.BackColor = Color.White
            KBMain.txtDET3.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtN16VFE1Current.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP3.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET4.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 13 Then
            'CH0=-16VFE2Current    CH1= -16VVolts   Latch1
            LATCHNUM = 0
            LATCHDATA = 24 + 4
            ProgLatch()

            'CH2=Det1     CH3=TEMP1     Latch2
            LATCHNUM = 1
            LATCHDATA = 0 + 0
            ProgLatch()

            'Get Data
            Read_Analog()
            KBMain.txtN16VFE2Current.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtN16VFE2Current.BackColor = Color.White
            KBMain.txtN16VFE1Current.BackColor = Color.LightGray
            KBMain.txtTEMP1.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP1.BackColor = Color.White
            KBMain.txtTEMP3.BackColor = Color.LightGray
            KBMain.txtDET1.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET1.BackColor = Color.White
            KBMain.txtDET4.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtN16VFE2Current.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP1.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET1.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 14 Then
            'CH0=-16VBE1Current    CH1= -16VVolts   Latch1
            LATCHNUM = 0
            LATCHDATA = 88 + 4
            ProgLatch()

            'CH2=Det2     CH3=TEMP2     Latch2
            LATCHNUM = 1
            LATCHDATA = 64 + 1
            ProgLatch()

            'Get Data
            Read_Analog()
            KBMain.txtN16VBE1Current.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtN16VBE1Current.BackColor = Color.White
            KBMain.txtN16VFE2Current.BackColor = Color.LightGray
            KBMain.txtTEMP2.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP2.BackColor = Color.White
            KBMain.txtTEMP1.BackColor = Color.LightGray
            KBMain.txtDET2.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET2.BackColor = Color.White
            KBMain.txtDET1.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtN16VBE1Current.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP2.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET2.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 15 Then
            'CH0=-16VBE2Current    CH1= -16VVolts   Latch1
            LATCHNUM = 0
            LATCHDATA = 56 + 4
            ProgLatch()

            'CH2=Det3     CH3=TEMP3     Latch2
            LATCHNUM = 1
            LATCHDATA = 32 + 2
            ProgLatch()

            'Get Data
            Read_Analog()
            KBMain.txtN16VBE2Current.Text = Format(ANALOG0 - IOffset, "0.000")
            KBMain.txtN16VBE2Current.BackColor = Color.White
            KBMain.txtN16VBE1Current.BackColor = Color.LightGray
            KBMain.txtTEMP3.Text = Format((ANALOG3 - ThermOffset) * ThermScale, "0.000")
            KBMain.txtTEMP3.BackColor = Color.White
            KBMain.txtTEMP2.BackColor = Color.LightGray
            KBMain.txtDET3.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET3.BackColor = Color.White
            KBMain.txtDET2.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtN16VBE2Current.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, KBMain.txtTEMP3.Text)
                Print(filenum3, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET3.Text)
                Print(filenum1, "  ")
            End If
        End If

        If i = 16 Then
            'CH0=-16VBE2Current    CH1= +12VVolts   Latch1
            LATCHNUM = 0
            LATCHDATA = 56 + 3
            ProgLatch()

            'CH2=Det4     CH3=TEMP1     Latch2
            LATCHNUM = 1
            LATCHDATA = 96 + 0
            ProgLatch()

            'Get Data
            Read_Analog()
            KBMain.txtN16VBE2Current.BackColor = Color.LightGray
            KBMain.txtP12VVolts.Text = Format(ANALOG1 * P12VScale, "0.000")
            KBMain.txtP12VVolts.BackColor = Color.White
            KBMain.txtN16VVolts.BackColor = Color.LightGray
            KBMain.txtDET4.Text = Format((ANALOG2 - DetOffset) * DetScale, "0.000")
            KBMain.txtDET4.BackColor = Color.White
            KBMain.txtDET3.BackColor = Color.LightGray

            If KBMain.RecTele.Checked = True Then
                Print(filenum, KBMain.txtP12VVolts.Text)
                Print(filenum, "  ")
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, KBMain.txtDET4.Text)
                Print(filenum1, "  ")
            End If
        End If

        i = i + 1
        If i > 16 Then
            i = 1
            If KBMain.RecTele.Checked = True Then
                Print(filenum, "\n")
                z = z + 1
                KBMain.IntCount.Text = Str(z)
                If z > 10000 Then
                    CloseTeleFile()
                    KBMain.RunCount.Text = Str(Val(KBMain.RunCount.Text) + 1)
                    OpenTeleFile()
                    z = 1
                    KBMain.IntCount.Text = Str(z)
                End If
            End If
            If KBMain.RecTemp.Checked = True Then
                Print(filenum3, "\n")
                z3 = z3 + 1
                If z3 > 10000 Then
                    CloseTempFile()
                    KBMain.RunCount1.Text = Str(Val(KBMain.RunCount1.Text) + 1)
                    OpenTempFile()
                    z3 = 1
                End If
            End If
            If KBMain.RecDet.Checked = True Then
                Print(filenum1, "\n")
                z1 = z1 + 1
                If z1 > 10000 Then
                    CloseDetFile()
                    KBMain.RunCount2.Text = Str(Val(KBMain.RunCount2.Text) + 1)
                    OpenDetFile()
                    z1 = 1
                End If
            End If
        End If
    End Sub
    Sub ProgLatch()
        'Write Latch Numner to EI00-EI07 (A0-A7)
        If LATCHNUM < 128 Then
            LJUD.eDO(lngHandle, 15, 0)
        Else
            LJUD.eDO(lngHandle, 15, 1)
            LATCHNUM = LATCHNUM - 128
        End If
        If LATCHNUM < 64 Then
            LJUD.eDO(lngHandle, 14, 0)
        Else
            LJUD.eDO(lngHandle, 14, 1)
            LATCHNUM = LATCHNUM - 64
        End If
        If LATCHNUM < 32 Then
            LJUD.eDO(lngHandle, 13, 0)
        Else
            LJUD.eDO(lngHandle, 13, 1)
            LATCHNUM = LATCHNUM - 32
        End If
        If LATCHNUM < 16 Then
            LJUD.eDO(lngHandle, 12, 0)
        Else
            LJUD.eDO(lngHandle, 12, 1)
            LATCHNUM = LATCHNUM - 16
        End If
        If LATCHNUM < 8 Then
            LJUD.eDO(lngHandle, 11, 0)
        Else
            LJUD.eDO(lngHandle, 11, 1)
            LATCHNUM = LATCHNUM - 8
        End If
        If LATCHNUM < 4 Then
            LJUD.eDO(lngHandle, 10, 0)
        Else
            LJUD.eDO(lngHandle, 10, 1)
            LATCHNUM = LATCHNUM - 4
        End If
        If LATCHNUM < 2 Then
            LJUD.eDO(lngHandle, 9, 0)
        Else
            LJUD.eDO(lngHandle, 9, 1)
            LATCHNUM = LATCHNUM - 2
        End If
        If LATCHNUM < 1 Then
            LJUD.eDO(lngHandle, 8, 0)
        Else
            LJUD.eDO(lngHandle, 8, 1)
        End If

        'Set SCK = 1    CI00
        'Set SDA = 1    CI01
        'Set NLOAD = 1  CI02
        'Set CSBUS = 0  CI03
        LJUD.eDO(lngHandle, 16, 1)
        LJUD.eDO(lngHandle, 17, 1)
        LJUD.eDO(lngHandle, 18, 1)
        LJUD.eDO(lngHandle, 19, 0)

        'Write Data
        If LATCHDATA < 128 Then
            LJUD.eDO(lngHandle, 17, 0)
        Else
            LJUD.eDO(lngHandle, 17, 1)
            LATCHDATA = LATCHDATA - 128
        End If

        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        If LATCHDATA < 64 Then
            LJUD.eDO(lngHandle, 17, 0)
        Else
            LJUD.eDO(lngHandle, 17, 1)
            LATCHDATA = LATCHDATA - 64
        End If

        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        If LATCHDATA < 32 Then
            LJUD.eDO(lngHandle, 17, 0)
        Else
            LJUD.eDO(lngHandle, 17, 1)
            LATCHDATA = LATCHDATA - 32
        End If

        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        If LATCHDATA < 16 Then
            LJUD.eDO(lngHandle, 17, 0)
        Else
            LJUD.eDO(lngHandle, 17, 1)
            LATCHDATA = LATCHDATA - 16
        End If

        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        If LATCHDATA < 8 Then
            LJUD.eDO(lngHandle, 17, 0)
        Else
            LJUD.eDO(lngHandle, 17, 1)
            LATCHDATA = LATCHDATA - 8
        End If

        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        If LATCHDATA < 4 Then
            LJUD.eDO(lngHandle, 17, 0)
        Else
            LJUD.eDO(lngHandle, 17, 1)
            LATCHDATA = LATCHDATA - 4
        End If

        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        If LATCHDATA < 2 Then
            LJUD.eDO(lngHandle, 17, 0)
        Else
            LJUD.eDO(lngHandle, 17, 1)
            LATCHDATA = LATCHDATA - 2
        End If

        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        If LATCHDATA < 1 Then
            LJUD.eDO(lngHandle, 17, 0)
        Else
            LJUD.eDO(lngHandle, 17, 1)
        End If

        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        'Set SCK = 1    CI00
        'Set SDA = 1    CI01
        'Set NLOAD = 1  CI02
        'Set CSBUS = 1  CI03
        LJUD.eDO(lngHandle, 16, 1)
        LJUD.eDO(lngHandle, 17, 1)
        LJUD.eDO(lngHandle, 18, 1)
        LJUD.eDO(lngHandle, 19, 1)

 
    End Sub
    Sub GetStatus()
        LATCHNUM = DigitalModule + 4
        ReadData()
        L1Status = MBDATA
        Digital.Latch1Data.Text = Str(L1Status)
        LATCHNUM = DigitalModule + 5
        ReadData()
        L2Status = MBDATA
        LATCHNUM = DigitalModule + 6
        ReadData()
        L3Status = MBDATA
        LATCHNUM = DigitalModule + 7
        ReadData()
        L4Status = MBDATA
    End Sub
    Sub Read_Analog()
        LJUD.eAIN(lngHandle, 0, 31, ANALOG0, 0, 0, 0, 0)
        LJUD.eAIN(lngHandle, 1, 31, ANALOG1, 0, 0, 0, 0)
        LJUD.eAIN(lngHandle, 2, 31, ANALOG2, 0, 0, 0, 0)
        LJUD.eAIN(lngHandle, 3, 31, ANALOG3, 0, 0, 0, 0)
        KBMain.txtSN.Text = Str(ANALOG3)
    End Sub
    Sub ReadData()
        MBDATA = 0
        'Write Latch Numner to EI00-EI07 (A0-A7)
        If LATCHNUM < 128 Then
            LJUD.eDO(lngHandle, 15, 0)
        Else
            LJUD.eDO(lngHandle, 15, 1)
            LATCHNUM = LATCHNUM - 128
        End If
        If LATCHNUM < 64 Then
            LJUD.eDO(lngHandle, 14, 0)
        Else
            LJUD.eDO(lngHandle, 14, 1)
            LATCHNUM = LATCHNUM - 64
        End If
        If LATCHNUM < 32 Then
            LJUD.eDO(lngHandle, 13, 0)
        Else
            LJUD.eDO(lngHandle, 13, 1)
            LATCHNUM = LATCHNUM - 32
        End If
        If LATCHNUM < 16 Then
            LJUD.eDO(lngHandle, 12, 0)
        Else
            LJUD.eDO(lngHandle, 12, 1)
            LATCHNUM = LATCHNUM - 16
        End If
        If LATCHNUM < 8 Then
            LJUD.eDO(lngHandle, 11, 0)
        Else
            LJUD.eDO(lngHandle, 11, 1)
            LATCHNUM = LATCHNUM - 8
        End If
        If LATCHNUM < 4 Then
            LJUD.eDO(lngHandle, 10, 0)
        Else
            LJUD.eDO(lngHandle, 10, 1)
            LATCHNUM = LATCHNUM - 4
        End If
        If LATCHNUM < 2 Then
            LJUD.eDO(lngHandle, 9, 0)
        Else
            LJUD.eDO(lngHandle, 9, 1)
            LATCHNUM = LATCHNUM - 2
        End If
        If LATCHNUM < 1 Then
            LJUD.eDO(lngHandle, 8, 0)
        Else
            LJUD.eDO(lngHandle, 8, 1)
        End If

        'Set SCK = 1    CI00
        'Set SDA = 1    CI01
        'Set NLOAD = 1  CI02
        'Set CSBUS = 0  CI03
        LJUD.eDO(lngHandle, 16, 1)
        LJUD.eDO(lngHandle, 17, 1)
        LJUD.eDO(lngHandle, 18, 1)
        LJUD.eDO(lngHandle, 19, 0)
        'Read Data
        'Cycle NLoad
        LJUD.eDO(lngHandle, 18, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 18, 1)
        'CEBUS Low
        LJUD.eDO(lngHandle, 19, 0)

        'Get Data 7
        LJUD.eDI(lngHandle, 7, DiValue)
        DiValue = DiValue And 1
        If DiValue = 1 Then
            MBDATA = 128
        End If
        'Cycle Clock
        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        'Get Data 6
        LJUD.eDI(lngHandle, 7, DiValue)
        DiValue = DiValue And 1
        If DiValue = 1 Then
            MBDATA = MBDATA + 64
        End If
        'Cycle Clock
        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        'Get Data 5
        LJUD.eDI(lngHandle, 7, DiValue)
        DiValue = DiValue And 1
        If DiValue = 1 Then
            MBDATA = MBDATA + 32
        End If
        'Cycle Clock
        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        'Get Data 4
        LJUD.eDI(lngHandle, 7, DiValue)
        DiValue = DiValue And 1
        If DiValue = 1 Then
            MBDATA = MBDATA + 16
        End If
        'Cycle Clock
        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        'Get Data 3
        LJUD.eDI(lngHandle, 7, DiValue)
        DiValue = DiValue And 1
        If DiValue = 1 Then
            MBDATA = MBDATA + 8
        End If
        'Cycle Clock
        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        'Get Data 2
        LJUD.eDI(lngHandle, 7, DiValue)
        DiValue = DiValue And 1
        If DiValue = 1 Then
            MBDATA = MBDATA + 4
        End If
        'Cycle Clock
        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        'Get Data 1
        LJUD.eDI(lngHandle, 7, DiValue)
        DiValue = DiValue And 1
        If DiValue = 1 Then
            MBDATA = MBDATA + 2
        End If
        'Cycle Clock
        LJUD.eDO(lngHandle, 16, 0)
        Sleep(10)
        LJUD.eDO(lngHandle, 16, 1)

        'Get Data 0
        LJUD.eDI(lngHandle, 7, DiValue)
        DiValue = DiValue And 1
        If DiValue = 1 Then
            MBDATA = MBDATA + 1
        End If
        'CEBUS High
        LJUD.eDO(lngHandle, 19, 1)

    End Sub
    Private Sub Initial_Gray()
        KBMain.txtP6VDVolts.BackColor = Color.LightGray
        KBMain.txtP6VAVolts.BackColor = Color.LightGray
        KBMain.txtP16VVolts.BackColor = Color.LightGray
        KBMain.txtN16VVolts.BackColor = Color.LightGray
        KBMain.txtP12VVolts.BackColor = Color.LightGray
        KBMain.txtTEMP1.BackColor = Color.LightGray
        KBMain.txtTEMP2.BackColor = Color.LightGray
        KBMain.txtTEMP3.BackColor = Color.LightGray
        KBMain.txtDET1.BackColor = Color.LightGray
        KBMain.txtDET2.BackColor = Color.LightGray
        KBMain.txtDET3.BackColor = Color.LightGray
        KBMain.txtDET4.BackColor = Color.LightGray
        KBMain.txtP6VDCurrent.BackColor = Color.LightGray
        KBMain.txtP6VACurrent.BackColor = Color.LightGray
        KBMain.txtP6VAFE1Current.BackColor = Color.LightGray
        KBMain.txtP6VAFE2Current.BackColor = Color.LightGray
        KBMain.txtP16ITotal.BackColor = Color.LightGray
        KBMain.txtP16VFE1Current.BackColor = Color.LightGray
        KBMain.txtP16VFE2Current.BackColor = Color.LightGray
        KBMain.txtP16VBE1Current.BackColor = Color.LightGray
        KBMain.txtP16VBE2Current.BackColor = Color.LightGray
        KBMain.txtP16VLOCurrent.BackColor = Color.LightGray
        KBMain.txtP16VD1Current.BackColor = Color.LightGray
        KBMain.txtN16VCurrent.BackColor = Color.LightGray
        KBMain.txtN16VFE1Current.BackColor = Color.LightGray
        KBMain.txtN16VFE2Current.BackColor = Color.LightGray
        KBMain.txtN16VBE1Current.BackColor = Color.LightGray
        KBMain.txtN16VBE2Current.BackColor = Color.LightGray

    End Sub
End Module
