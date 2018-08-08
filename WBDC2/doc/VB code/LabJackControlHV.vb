Option Explicit On

Imports System.Threading.Thread

' Import the UD .NET wrapper object.  The dll referenced is installed by the
' LabJackUD installer.
Imports LabJack.LabJackUD



Public Class LabJackControlHV
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

        LJUD.OpenLabJack(LJUD.DEVICE.U3, LJUD.CONNECTION.USB, "0", 1, lngHandle)

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

        LJUD.eAIN(lngHandle, 0, 31, dblAIN0, 0, 0, 0, 0)
        LJUD.eAIN(lngHandle, 1, 31, dblAIN1, 0, 0, 0, 0)
        LJUD.eAIN(lngHandle, 2, 31, dblAIN2, 0, 0, 0, 0)
        LJUD.eAIN(lngHandle, 3, 31, dblAIN3, 0, 0, 0, 0)
        txtAIN0.Text = Format(dblAIN0, "#.#####")
        txtAIN1.Text = Format(dblAIN1, "#.#####")
        txtAIN2.Text = Format(dblAIN2, "#.#####")
        txtAIN3.Text = Format(dblAIN3, "#.#####")

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