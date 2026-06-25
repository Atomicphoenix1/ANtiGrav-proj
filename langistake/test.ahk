#NoTrayIcon
#include C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\langistake\EngArConverter.ahk

Output := ""
; Test 1: English "Hello guys" -> Arabic
str := "Hello guys"
Output := Output . "Input: " . str . "`n"
conv := ""
Loop, Parse, str
{
    ch := A_LoopField
    if (ch = "b" or ch = "B") {
        conv := conv . "لا"
    } else {
        conv := conv . En2Ar(ch)
    }
}
Output := Output . "En->Ar: " . conv . "`n`n"

; Test 2: Arabic back -> English
Input2 := conv
Output := Output . "Input: " . Input2 . "`n"
conv2 := ""
i := 1
len := StrLen(Input2)
while (i <= len) {
    ch := SubStr(Input2, i, 1)
    nxt := SubStr(Input2, i + 1, 1)
    if (ch = "ل" and nxt = "ا") {
        conv2 := conv2 . "b"
        i := i + 2
    } else {
        conv2 := conv2 . Ar2En(ch)
        i := i + 1
    }
}
Output := Output . "Ar->En: " . conv2 . "`n`n"

; Test 3: b/B special
bb := "bB"
Output := Output . "b/B -> "
bbout := ""
Loop, Parse, bb
{
    ch := A_LoopField
    if (ch = "b" or ch = "B") {
        bbout := bbout . "لا"
    } else {
        bbout := bbout . En2Ar(ch)
    }
}
Output := Output . bbout . "`n"

; Test 4: لا -> b
Output := Output . "لا -> "
la_input := bbout
la_out := ""
i := 1
len := StrLen(la_input)
while (i <= len) {
    ch := SubStr(la_input, i, 1)
    nxt := SubStr(la_input, i + 1, 1)
    if (ch = "ل" and nxt = "ا") {
        la_out := la_out . "b"
        i := i + 2
    } else {
        la_out := la_out . Ar2En(ch)
        i := i + 1
    }
}
Output := Output . la_out . "`n"

FileAppend, %Output%, %A_ScriptDir%\test_result.txt
ExitApp
