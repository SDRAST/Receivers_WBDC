'LabJack Varables
'Labjack Digital Definitions
'FI00   CH0     CH0 IMON
'FIO1   CH1     CH1 VMON
'FIO2   CH2     CH3 TEMP
'FI03   CH3     Ch4 LNA
'FI04   CH4
'FI05   CH5
'FI06   CH6
'FI07   CH7     SDO
'EI00   CH8     A0
'EI01   CH9     A1
'Ei02   CH10    A2
'EI03   CH11    A3
'EI04   CH12    A4
'EI05   CH13    A5
'EI06   CH14    A6
'EI07   CH15    A7
'CI00   CH16    SCK
'CI01   CH17    SDI
'CI02   CH18    NLOAD
'CI03   CH19    CS-BUS
Imports LabJack.LabJackUD
Module LabJack

    Sub Initial_LabJack0()
        'Open the first found LabJack U3 over USB.
        LJUD.OpenLabJack(LJUD.DEVICE.U3, LJUD.CONNECTION.USB, "0", 1, lngHandle)
        KBMain.txtOpenErrorNumber.Text = Str(lngError)
        KBMain.txtOpenErrorNumber.Refresh()
        'Convert the error code to a string.
        LJUD.ErrorToString(lngError, strError)
        KBMain.txtOpenErrorString.Text = strError
        KBMain.txtOpenErrorString.Refresh()
    End Sub
    Sub Initial_LabJack1()
        'Open LabJack #1
        Try
            LJUD.OpenLabJack(LJUD.DEVICE.U3, LJUD.CONNECTION.USB, "1", 0, lngHandle)
        Catch ex As LabJackUDException
            KBMain.showErrorMessage(ex)
        End Try
    End Sub
    Sub Initial_LabJack2()
        'Open LabJack #2
        Try
            LJUD.OpenLabJack(LJUD.DEVICE.U3, LJUD.CONNECTION.USB, "2", 0, lngHandle2)
        Catch ex As LabJackUDException
            KBMain.showErrorMessage(ex)
        End Try
    End Sub
    Sub Initial_LabJack3()
        'Open LabJack #3
        Try
            LJUD.OpenLabJack(LJUD.DEVICE.U3, LJUD.CONNECTION.USB, "3", 0, lngHandle3)
        Catch ex As LabJackUDException
            KBMain.showErrorMessage(ex)
        End Try
    End Sub
End Module
