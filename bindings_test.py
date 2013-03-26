#MAEC v1.1 Bindings Test
#Iterates through each Behavior in a Bundle and prints the Description Text

import maecv11 as maec_binding

maec_bundle = maec_binding.parse('analysis.xml')

for behavior in maec_bundle.Behaviors.Behavior:
    print behavior.Description.Text