from troposphere import GetAtt, Join, Output, If, Equals, Condition
from troposphere import Parameter, Ref, Template, Export, Sub
import troposphere.elasticsearch as elasticsearch


t = Template()
def main():
    # Meta
    t.add_version("2010-09-09")
    t.add_description("Elasticsearch template")
    t.add_metadata({
        "Comments": "",
        "LastUpdated": "2017 01 23",
        "UpdatedBy": "Hamin Mousavi",
        "Version": "1",
    })
    # Elastisearch
    elasticsearch_domain_name = t.add_parameter(Parameter(
        "elasticsearchDomainName",
        Type="String",
        Description="What is your Elasticsearch domain called?",
        AllowedPattern="[a-z][a-z0-9\-]+",
    ))
    elasticsearch_dedicated_master_instances = t.add_parameter(Parameter(
        "elasticsearchDedicatedMasterInstances",
        Default="2",
        Type="Number",
        Description="Number of Elasticsearch Dedicated Master instances. (Must be > 2)"
    ))
    elastisearch_instances = t.add_parameter(Parameter(
        "elastisearchInstances",
        Default="4",
        Type="Number",
        Description="Even number of Elastisearch instances",
        ConstraintDescription="Even positive numbers only"
    ))
    elasticsearch_instance_type = t.add_parameter(Parameter(
        "elasticsearchInstanceType",
        Default="t2.micro.elasticsearch",
        Type="String",
        Description="Which Elasticsearch instance type do you want to use?",
        AllowedValues=[
            "t2.micro.elasticsearch",
            "t2.small.elasticsearch",
            "t2.medium.elasticsearch",
            "m3.medium.elasticsearch",
            "m3.large.elasticsearch",
            "m3.xlarge.elasticsearch",
            "m3.2xlarge.elasticsearch",
            "r3.large.elasticsearch",
            "r3.xlarge.elasticsearch",
            "r3.2xlarge.elasticsearch",
            "r3.4xlarge.elasticsearch",
            "r3.8xlarge.elasticsearch",
            "i2.xlarge.elasticsearch",
            "i2.2xlarge.elasticsearch",
        ],
        ConstraintDescription="http://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-createupdatedomains.html#es-createdomains-configure-cluster-cli",
    ))

    # Elasticsearch EBS Volume conditional
    use_ebs_volume = t.add_parameter(Parameter(
        "useEbsVolume",
        Type="String",
        Description="Use EBS volumes with Elasticsearch data instances (True/False)",
        Default="True",
        AllowedValues=[
            "True",
            "False"
        ],
        ConstraintDescription="True or False"
    ))
    t.add_condition(
        "EbsTrue",
        Equals(
            Ref(use_ebs_volume),
            "True"
            )
    )

    elasticsearch_ebs_volumesize = t.add_parameter(Parameter(
        "elasticsearchEbsVolumesize",
        Default="20",
        Type="Number",
        Description="How large EBS volume should each data-node have? (GB)"
    ))
    elasticsearch_snapshot_time = t.add_parameter(Parameter(
        "elasticsearchSnapshotTime",
        Default="0",
        Type="Number",
        Description="When should automatic snapshots be taken of the Elasticsearch domain? (0-23)"
    ))
    elasticsearch_version = t.add_parameter(Parameter(
        "elasticsearchVersion",
        Default="2.3",
        Type="String",
        AllowedValues=[
            "1.5",
            "2.3"
        ],
        Description="AWS Elasticsearch version"
    ))
    elasticsearch_domain = t.add_resource(elasticsearch.Domain(
        'ElasticsearchDomain',
        DomainName=Ref(elasticsearch_domain_name),
        ElasticsearchVersion=Ref(elasticsearch_version),
        ElasticsearchClusterConfig=elasticsearch.ElasticsearchClusterConfig(
            DedicatedMasterEnabled=True,
            InstanceCount=Ref(elastisearch_instances),
            ZoneAwarenessEnabled=True,
            InstanceType=Ref(elasticsearch_instance_type),
            DedicatedMasterType=Ref(elasticsearch_instance_type),
            DedicatedMasterCount=Ref(elasticsearch_dedicated_master_instances)
        ),
        EBSOptions=elasticsearch.EBSOptions(
            EBSEnabled=If("EbsTrue", Ref(use_ebs_volume), Ref("AWS::NoValue")),
            VolumeSize=If("EbsTrue", Ref(elasticsearch_ebs_volumesize), Ref("AWS::NoValue")),
        ),
        SnapshotOptions=elasticsearch.SnapshotOptions(
            AutomatedSnapshotStartHour=Ref(elasticsearch_snapshot_time)
            ),
        AccessPolicies={'Version': '2012-10-17',
                        'Statement': [{
                            'Effect': 'Allow',
                            'Principal': {
                                'AWS': '*'
                            },
                            'Action': 'es:*',
                            'Resource': '*'
                        }]},
        AdvancedOptions={"rest.action.multi.allow_explicit_index": "true"}
    ))

    t.add_output(
        Output(
            "URL",
            Description="Elasticsearch URI",
            Value=Join(":", [
                GetAtt(elasticsearch_domain, "DomainEndpoint"),
            ]),
            Export=Export(Sub("${AWS::StackName}-URI")),
        )
    )
    print(t.to_json())

if __name__ == '__main__':
    main()
