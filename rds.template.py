from troposphere import GetAtt, Join, Output, Parameter, Ref, Template, FindInMap, Not, Equals, If, Export, Sub
import troposphere.ec2 as ec2
import troposphere.rds as rds

t = Template()

# Database engines and engine versions
def engineVersionList(template):
    t.add_mapping("engineVersionList", {
        "postgres": {"Version": "9.5.4"},
        "sqlserver-ee": {"Version": "13.00.2164.0.v1"},
        "sqlserver-se": {"Version": "13.00.2164.0.v1"},
        "sqlserver-ex": {"Version": "13.00.2164.0.v1"},
        "sqlserver-web": {"Version": "13.00.2164.0.v1"}
    })


def engineLicenseList(template):
    t.add_mapping("engineLicenseList", {
        "postgres": {"License": "postgresql-license"},
        "sqlserver-ee": {"License": "license-included"},
        "sqlserver-se": {"License": "license-included"},
        "sqlserver-ex": {"License": "license-included"},
        "sqlserver-web": {"License": "license-included"}
    })


def main():
    # Meta
    t.add_version("2010-09-09")
    t.add_description("RDS template for PostgreSQL and SQL server")
    t.add_metadata({
        "Comments": "",
        "LastUpdated": "2017 01 24",
        "UpdatedBy": "Hamin Mousavi",
        "Version": "1",
    })

    engineVersionList(t)
    engineLicenseList(t)

    # VPC
    subnets = t.add_parameter(Parameter(
        "subnets",
        Type="List<AWS::EC2::Subnet::Id>",
        Description=" Subnets to use for the database"
    ))
    vpc = t.add_parameter(Parameter(
        "VPC",
        Type="AWS::EC2::VPC::Id",
        Description="Environment VPC"
    ))

    # RDS
    existing_db_snapshot = t.add_parameter(Parameter(
        "existingDbSnapshot",
        Type="String",
        Description="Existing Db snapshot to restore, leave blank to create a new",
        Default=""
    ))
    db_multiaz = t.add_parameter(Parameter(
        "dbMultiAz",
        Type="String",
        Description="Multi AZ True/False for automatic failover if one availability zone goes down",
        Default="False"
    ))
    db_name = t.add_parameter(Parameter(
        "dbName",
        Default="",
        Description="sqlserver-ex/web/se/ee = No name.",
        Type="String",
    ))
    db_user = t.add_parameter(Parameter(
        "dbUser",
        NoEcho=True,
        Description="The database admin account username",
        Type="String",
        MinLength="1",
        MaxLength="16",
        AllowedPattern="[a-zA-Z][a-zA-Z0-9]*",
        ConstraintDescription=("Must begin with a letter and contain only"
                               " alphanumeric characters.")
    ))
    db_password = t.add_parameter(Parameter(
        "dbPassword",
        NoEcho=True,
        Description="The database admin account password",
        Type="String",
        MinLength="0",
        MaxLength="41",
        AllowedPattern="[a-zA-Z0-9]*",
        ConstraintDescription="Must contain only alphanumeric characters. If you are restoring a snapshot leave this blank."
    ))
    db_class = t.add_parameter(Parameter(
        "dbClass",
        Default="db.t2.small",
        Description="T = Small; M = Memory; R = CPU",
        Type="String",
        AllowedValues=[
            "db.t2.small",
            "db.t2.micro",
            "db.t2.medium",
            "db.t2.large",
            "db.m4.large",
            "db.m4.xlarge",
            "db.m4.2xlarge",
            "db.m4.4xlarge",
            "db.m4.10xlarge",
            "db.r3.large",
            "db.r3.xlarge",
            "db.r3.2xlarge",
            "db.r3.4xlarge",
            "db.r3.8xlarge",
        ],
        ConstraintDescription="Must select a valid database instance type.",
    ))

    db_allocatedstorage = t.add_parameter(Parameter(
        "dbAllocatedstorage",
        Default="20",
        Description="postgresql 5 < 6000 GB, sqlserver-ex/web 20 < 200 GB, sqlserver-se/ee 200 < 4000 GB",
        Type="Number",
        MinValue="5"
    ))
    db_engine = t.add_parameter(Parameter(
        "dbEngine",
        Default="postgres",
        Type="String",
        Description="Which database type do you want to use?",
        AllowedValues=[
            "postgres",
            "sqlserver-ex",
            "sqlserver-web",
            "sqlserver-se",
            "sqlserver-ee",
        ],
        ConstraintDescription="postgres, sqlserver-ex/web/se/ee",
    ))
    db_subnetgroup = t.add_resource(rds.DBSubnetGroup(
        "dbSubnetgroup",
        DBSubnetGroupDescription="Subnets available for the RDS DB Instance",
        SubnetIds=Ref(subnets),
    ))

    vpc_securitygroup = t.add_resource(ec2.SecurityGroup(
        "vpcSecuritygroup",
        GroupDescription="Security group for RDS DB Instance.",
        VpcId=Ref(vpc),
        SecurityGroupIngress=[
            # The Whole VPC
            ec2.SecurityGroupRule(
                IpProtocol="tcp",
                FromPort="0",
                ToPort="65535",
                CidrIp="10.0.0.0/16"
            )
        ]
    ))
    restore_snapshot = "RestoreSnapshot"

    t.add_condition(
        restore_snapshot,
        Not(Equals(Ref(existing_db_snapshot), existing_db_snapshot.Default))
    )
    db = t.add_resource(rds.DBInstance(
        "db",
        DBName=If(
            restore_snapshot,
            Ref("AWS::NoValue"),
            Ref(db_name)
        ),
        AllocatedStorage=If(
            restore_snapshot,
            Ref("AWS::NoValue"),
            Ref(db_allocatedstorage)
        ),
        DBSnapshotIdentifier=If(
            restore_snapshot,
            Ref(existing_db_snapshot),
            Ref("AWS::NoValue")
        ),
        DBInstanceClass=Ref(db_class),
        Engine=If(
            restore_snapshot,
            Ref("AWS::NoValue"),
            Ref(db_engine)
        ),
        EngineVersion=FindInMap("engineVersionList", Ref(db_engine), "Version"),
        MasterUsername=If(
            restore_snapshot,
            Ref("AWS::NoValue"),
            Ref(db_user)
        ),
        MasterUserPassword=If(
            restore_snapshot,
            Ref("AWS::NoValue"),
            Ref(db_password),
        ),
        DBSubnetGroupName=Ref(db_subnetgroup),
        VPCSecurityGroups=[Ref(vpc_securitygroup)],
        MultiAZ=Ref(db_multiaz),
        LicenseModel=FindInMap("engineLicenseList", Ref(db_engine), "License")
    ))

    db.DeletionPolicy = "Snapshot"

    t.add_output(Output(
        "JDBCConnectionString",
        Description="JDBC connection string for database",
        Value=Join("", [
            GetAtt("db", "Endpoint.Address"),
            ":",
            GetAtt("db", "Endpoint.Port"),
            "/",
            Ref(db_name)
        ]),
        Export=Export(Sub("${AWS::StackName}-RDS")),
    ))

    print(t.to_json())

if __name__ == '__main__':
    main()