Option Explicit On

Imports System.Threading.Thread

' Import the UD .NET wrapper object.  The dll referenced is installed by the
' LabJackUD installer.
Imports LabJack.LabJackUD

Public Class LabJackControlLV
    Inherits System.Windows.Forms.Form

    Sub ErrorMessage(ByVal err As LabJackUDException)
        MsgBox("Function returned LabJackUD Error #" & _
            Str$(err.LJUDError) & _
            "  " & _
            err.ToString)
    End Sub
    Private Sub cmdInitialize_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles cmdInitialize.Click

        z = 1
        'Retrieve the LabJackUD driver version.
        dblDriverVersion = LJUD.GetDriverVersion()
        txtDriverVersion.Text = Str(dblDriverVersion)
        textDNDriverVersion.Text = LJUD.LJUDDOTNET_VERSION
        'Open the first found LabJack U3 over USB.

        'LJUD.OpenLabJack(LJUD.DEVICE.U3, LJUD.CONNECTION.USB, "0", 1, lngHandle)
        Initial_LabJack1()
        txtHandle.Text = Str(lngHandle)
        txtOpenErrorNumber.Text = Str(lngError)
        'Convert the error code to a string.
        LJUD.ErrorToString(lngError, strError)
        txtOpenErrorString.Text = strError
        'Read and display the serial number.
        LJUD.eGet(lngHandle, LJUD.IO.GET_CONFIG, LJUD.CHANNEL.SERIAL_NUMBER, dblSerialNumber, 0)
        txtSerialNumber.Text = Str(dblSerialNumber)

        dblDAC0 = Val(txtDAC0.Text)
        dblDAC1 = Val(txtDAC1.Text)
        LJUD.eDAC(lngHandle, 0, dblDAC0, 0, 0, 0)
        LJUD.eDAC(lngHandle, 1, dblDAC1, 0, 0, 0)

        Sleep(100)

        If FIO0OUT.Checked = False Then
            LJUD.eDI(lngHandle, 0, digFIO0)
            If digFIO0 = 0 Then
                FIO0.Checked = False
            End If
            If digFIO0 = 1 Then
                FIO0.Checked = True
            End If
        Else
            If FIO0.Checked = False Then
                LJUD.eDO(lngHandle, 0, 0)
            Else
                LJUD.eDO(lngHandle, 0, 1)
            End If
        End If

        If FIO0OUT.Checked = False Then
            LJUD.eDI(lngHandle, 1, digFIO1)
            If digFIO1 = 0 Then
                FIO1.Checked = False
            End If
            If digFIO1 = 1 Then
                FIO1.Checked = True
            End If
        Else
            If FIO1.Checked = False Then
                LJUD.eDO(lngHandle, 1, 0)
            Else
                LJUD.eDO(lngHandle, 1, 1)
            End If
        End If

        If FIO2OUT.Checked = False Then
            LJUD.eDI(lngHandle, 2, digFIO2)
            If digFIO2 = 0 Then
                FIO2.Checked = False
            End If
            If digFIO2 = 1 Then
                FIO2.Checked = True
            End If
        Else
            If FIO2.Checked = False Then
                LJUD.eDO(lngHandle, 2, 0)
            Else
                LJUD.eDO(lngHandle, 2, 1)
            End If
        End If

        If FIO3OUT.Checked = False Then
            LJUD.eDI(lngHandle, 3, digFIO3)
            If digFIO3 = 0 Then
                FIO3.Checked = False
            End If
            If digFIO3 = 1 Then
                FIO3.Checked = True
            End If
        Else
            If FIO3.Checked = False Then
                LJUD.eDO(lngHandle, 3, 0)
            Else
                LJUD.eDO(lngHandle, 3, 1)
            End If
        End If

        If FIO4OUT.Checked = False Then
            LJUD.eDI(lngHandle, 4, digFIO4)
            If digFIO4 = 0 Then
                FIO4.Checked = False
            End If
            If digFIO4 = 1 Then
                FIO4.Checked = True
            End If
        Else
            If FIO4.Checked = False Then
                LJUD.eDO(lngHandle, 4, 0)
            Else
                LJUD.eDO(lngHandle, 4, 1)
            End If
        End If

        If FIO5OUT.Checked = False Then
            LJUD.eDI(lngHandle, 5, digFIO5)
            If digFIO5 = 0 Then
                FIO5.Checked = False
            End If
            If digFIO5 = 1 Then
                FIO5.Checked = True
            End If
        Else
            If FIO5.Checked = False Then
                LJUD.eDO(lngHandle, 5, 0)
            Else
                LJUD.eDO(lngHandle, 5, 1)
            End If
        End If

        If FIO6OUT.Checked = False Then
            LJUD.eDI(lngHandle, 6, digFIO6)
            If digFIO6 = 0 Then
                FIO6.Checked = False
            End If
            If digFIO6 = 1 Then
                FIO6.Checked = True
            End If
        Else
            If FIO6.Checked = False Then
                LJUD.eDO(lngHandle, 6, 0)
            Else
                LJUD.eDO(lngHandle, 6, 1)
            End If
        End If

        If FIO7OUT.Checked = False Then
            LJUD.eDI(lngHandle, 7, digFIO7)
            If digFIO7 = 0 Then
                FIO7.Checked = False
            End If
            If digFIO7 = 1 Then
                FIO7.Checked = True
            End If
        Else
            If FIO7.Checked = False Then
                LJUD.eDO(lngHandle, 7, 0)
            Else
                LJUD.eDO(lngHandle, 7, 1)
            End If
        End If
    End Sub

End Class