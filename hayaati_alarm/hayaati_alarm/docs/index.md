# Introduction

HayaatiAlarm for Flet.

## Examples

```
import flet as ft

from hayaati_alarm import HayaatiAlarm


def main(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(

                ft.Container(height=150, width=300, alignment = ft.Alignment.CENTER, bgcolor=ft.Colors.PURPLE_200, content=HayaatiAlarm(
                    tooltip="My new HayaatiAlarm Control tooltip",
                    value = "My new HayaatiAlarm Flet Control",
                ),),

    )


ft.run(main)
```

## Classes

[HayaatiAlarm](HayaatiAlarm.md)
