from troposphere import Template, Parameter, AWS_REGION, Ref
import troposphere.route53 as route53

t = Template()
t.add_version("2010-09-09")
t.add_description(""" Private DNS """)

DNS = t.add_parameter(Parameter(
    "DNS",
    Default="",
    Type="String",
    Description="Define the environment for the hosted zone"
))

VPC = t.add_parameter(Parameter(
    "VPC",
    Default="",
    Type="AWS::EC2::VPC::Id",
    Description="Environment VPC"
))

t.add_resource(route53.HostedZone("HostedZone",
    HostedZoneConfig=route53.HostedZoneConfiguration(
        Comment="Internal hosted zone",
    ),
    Name=Ref(DNS),
    VPCs=[
      route53.HostedZoneVPCs(VPCId=Ref(VPC), VPCRegion=Ref(AWS_REGION))
    ]
))

print(t.to_json())