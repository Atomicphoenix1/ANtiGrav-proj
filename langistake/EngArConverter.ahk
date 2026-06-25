#!Space::
    OldClipboard := ClipboardAll
    Clipboard := ""
    SendInput ^c
    ClipWait 1
    if ErrorLevel {
        Clipboard := OldClipboard
        return
    }

    Text := Clipboard
    Clipboard := ""

    HasArabic := false
    Loop, Parse, Text
    {
        c := Ord(A_LoopField)
        if (c >= 0x0600 && c <= 0x06FF) {
            HasArabic := true
            break
        }
    }

    Result := ""
    if HasArabic {
        i := 1
        len := StrLen(Text)
        while (i <= len) {
            ch := SubStr(Text, i, 1)
            nxt := SubStr(Text, i + 1, 1)
            if (ch = "ل" and nxt = "ا") {
                Result .= "b"
                i += 2
            } else {
                Result .= Ar2En(ch)
                i += 1
            }
        }
    } else {
        Loop, Parse, Text
        {
            ch := A_LoopField
            if (ch = "b" or ch = "B") {
                Result .= "لا"
            } else {
                Result .= En2Ar(ch)
            }
        }
    }

    Clipboard := Result
    Sleep 200
    SendInput ^v
    Sleep 200
    Clipboard := OldClipboard
return

InitEn2Ar() {
    global EA
    EA := {}
    EA["a"] := "ش"
    EA["b"] := "ل"
    EA["c"] := "ؤ"
    EA["d"] := "ي"
    EA["e"] := "ث"
    EA["f"] := "ب"
    EA["g"] := "ل"
    EA["h"] := "ا"
    EA["i"] := "ه"
    EA["j"] := "ت"
    EA["k"] := "ن"
    EA["l"] := "م"
    EA["m"] := "ة"
    EA["n"] := "ى"
    EA["o"] := "خ"
    EA["p"] := "ح"
    EA["q"] := "ض"
    EA["r"] := "ق"
    EA["s"] := "س"
    EA["t"] := "ف"
    EA["u"] := "ع"
    EA["v"] := "ر"
    EA["w"] := "ص"
    EA["x"] := "ء"
    EA["y"] := "غ"
    EA["z"] := "ئ"
    EA["A"] := "ش"
    EA["B"] := "ل"
    EA["C"] := "ؤ"
    EA["D"] := "ي"
    EA["E"] := "ث"
    EA["F"] := "ب"
    EA["G"] := "ل"
    EA["H"] := "ا"
    EA["I"] := "ه"
    EA["J"] := "ت"
    EA["K"] := "ن"
    EA["L"] := "م"
    EA["M"] := "ة"
    EA["N"] := "ى"
    EA["O"] := "خ"
    EA["P"] := "ح"
    EA["Q"] := "ض"
    EA["R"] := "ق"
    EA["S"] := "س"
    EA["T"] := "ف"
    EA["U"] := "ع"
    EA["V"] := "ر"
    EA["W"] := "ص"
    EA["X"] := "ء"
    EA["Y"] := "غ"
    EA["Z"] := "ئ"
    EA["["] := "ج"
    EA["{"] := "ج"
    EA["]"] := "د"
    EA["}"] := "د"
    EA[";"] := "ك"
    EA[":"] := "ك"
    EA["'"] := "ط"
    DQ := Chr(34)
    EA[DQ] := "ط"
    EA[","] := "و"
    EA["<"] := "و"
    EA["."] := "ز"
    EA[">"] := "ز"
    EA["/"] := "ظ"
    EA["?"] := "ظ"
    EA["\"] := "ذ"
    EA["|"] := "ذ"
}

InitAr2En() {
    global AE
    AE := {}
    AE["ض"] := "q"
    AE["ص"] := "w"
    AE["ث"] := "e"
    AE["ق"] := "r"
    AE["ف"] := "t"
    AE["غ"] := "y"
    AE["ع"] := "u"
    AE["ه"] := "i"
    AE["خ"] := "o"
    AE["ح"] := "p"
    AE["ج"] := "["
    AE["د"] := "]"
    AE["ش"] := "a"
    AE["س"] := "s"
    AE["ي"] := "d"
    AE["ب"] := "f"
    AE["ل"] := "g"
    AE["ا"] := "h"
    AE["ت"] := "j"
    AE["ن"] := "k"
    AE["م"] := "l"
    AE["ك"] := ";"
    AE["ط"] := "'"
    AE["ئ"] := "z"
    AE["ء"] := "x"
    AE["ؤ"] := "c"
    AE["ر"] := "v"
    AE["ى"] := "n"
    AE["ة"] := "m"
    AE["و"] := ","
    AE["ز"] := "."
    AE["ظ"] := "/"
    AE["ذ"] := "\"
}

InitEn2Ar()
InitAr2En()

En2Ar(c) {
    global EA
    if EA.HasKey(c)
        return EA[c]
    return c
}

Ar2En(c) {
    global AE
    if AE.HasKey(c)
        return AE[c]
    return c
}
