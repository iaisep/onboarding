from apirest.models import restrictiva, puntaje
import pandas as pd
from fuzzywuzzy import fuzz
# -*- coding: utf-8 -*-



class consult2:
    def llegar(self, n,s):
        name_algo =''
        self.name_algo = n + ' p'
        return name_algo

    def comparar(self,n1):
        indices = [0]
        sancionados = {'nombres': "", 'Puntos': 0, 'Lista_Sanciones': "", 'Prospecto': ''}
        puntos = int(puntaje.objects.get(pk=1).puntaje_Max)
        df = pd.DataFrame(data=sancionados, index=indices)
        self.sancionados = df
        for name in restrictiva.objects.all():
                c = str(name.name)
                ca = c.upper()
                a = str(n1)
                aa = a.upper()
                listas = name.list
                result = fuzz.partial_ratio(aa, ca)
                if result >= puntos:
                    nuevo_registro = {'id': int(name.id), 'nombres': ca,
                                      'Puntos': result, 'Lista_Sanciones': listas,
                                      'Prospecto': n1}
                    df = df.append(nuevo_registro, ignore_index=True)
                    self.sancionados = df[df.Puntos != 0]
                else:
                    pass
        self.sancionados = df[df.Puntos != 0]
        return sancionados






