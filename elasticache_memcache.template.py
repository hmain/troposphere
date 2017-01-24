from troposphere import Select, GetAtt, Join, Output
from troposphere import Parameter, Ref, Template, Export, Sub
import troposphere.ec2 as ec2
import troposphere.elasticache as elasticache


t = Template()

def main():
    # Meta
    t.add_version("2010-09-09")
    t.add_description("Elasticache memcached template")
    t.add_metadata({
        "Comments": "",
        "LastUpdated": "2017 01 24",
        "UpdatedBy": "Hamin Mousavi",
        "Version": "1",
    })
    # Parameter grouping
    t.add_metadata(
        {
            "AWS::CloudFormation::Interface": {
                "ParameterGroups": [
                    {
                        "Label": {"default": "VPC"},
                        "Parameters": ["VPC",
                                       "security_group"]
                    },
                    {
                        "Label": {"default": "Elasticache"},
                        "Parameters": ["cacheSubnets",
                                       "numberOfCacheNodes",
                                       "cacheNodeType",
                                       "cacheSecurityGroup",
                                       "cacheSubnetGroup",
                                       "cacheCluster",
                                       "cacheParameters"]
                    },
                ]
            }
        }
    )
    # VPC
    vpc = t.add_parameter(Parameter(
        "VPC",
        Type="AWS::EC2::VPC::Id",
        Description="Environment VPC"
    ))

    security_group = t.add_parameter(Parameter(
        "securityGroup",
        Type="List<AWS::EC2::SecurityGroup::Id>",
        Description="Which security groups to use"
    ))

    # Elasticache
    cache_subnets = t.add_parameter(Parameter(
        "cacheSubnets",
        Type="List<AWS::EC2::Subnet::Id>",
        Description="Private subnets for the elasticache."
    ))

    number_of_cache_nodes = t.add_parameter(Parameter(
        "numberOfCacheNodes",
        Description="The number of Cache Nodes the Cache Cluster should have",
        Default="1",
        Type="Number",
        MaxValue="10",
        MinValue="1",
        ConstraintDescription="Must be between 1 and 10.",
    ))

    cache_node_type = t.add_parameter(Parameter(
        "cacheNodeType",
        Default="cache.t2.micro",
        ConstraintDescription="Must select a valid Cache Node type.",
        Type="String",
        Description="T = Small, M = General, C = CPU, R = Memory",
        AllowedValues=["cache.t2.micro",
                       "cache.t2.small",
                       "cache.t2.medium",
                       "cache.m4.large",
                       "cache.m4.xlarge",
                       "cache.m4.2xlarge",
                       "cache.m4.4xlarge",
                       "cache.m4.10xlarge",
                       "cache.c1.xlarge",
                       "cache.r3.large",
                       "cache.r3.xlarge",
                       "cache.r3.2xlarge",
                       "cache.r3.4xlarge",
                       "cache.r3.8xlarge"
                      ],
    ))

    cache_security_group = t.add_resource(ec2.SecurityGroup(
        "cacheSecurityGroup",
        SecurityGroupIngress=[{
            "ToPort": "65535",
            "IpProtocol": "tcp",
            "SourceSecurityGroupId": Select("0", Ref(security_group)),
            "FromPort": "0"}],
        VpcId=Ref(vpc),
        GroupDescription="Allow access to the cache from selected security groups",
    ))

    cache_subnet_group = t.add_resource(elasticache.SubnetGroup(
        "cacheSubnetGroup",
        SubnetIds=Ref(cache_subnets),
        Description="Subnets available for the ElastiCache Cluster",
    ))

    cache_parameters = t.add_resource(elasticache.ParameterGroup(
        "cacheParameters",
        Properties={
            "cas_disabled": "1"},
        CacheParameterGroupFamily="memcached1.4",
        Description="Elasticache memcached parameter group",
    ))

    cache_cluster = t.add_resource(elasticache.CacheCluster(
        "cacheCluster",
        Engine="memcached",
        NumCacheNodes=Ref(number_of_cache_nodes),
        CacheNodeType=Ref(cache_node_type),
        VpcSecurityGroupIds=[Ref(cache_security_group)],
        CacheSubnetGroupName=Ref(cache_subnet_group),
        CacheParameterGroupName=Ref(cache_parameters)
    ))

    t.add_output(
        Output(
            "URL",
            Description="Elasticache URI",
            Value=Join(":", [
                GetAtt(cache_cluster, "ConfigurationEndpoint.Address"),
                GetAtt(cache_cluster, "ConfigurationEndpoint.Port"),
            ]),
            Export=Export(Sub("${AWS::StackName}-URI")),
        )
    )

print(t.to_json())

if __name__ == '__main__':
    main()
