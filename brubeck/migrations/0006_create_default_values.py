# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        """ Adds `boolean` value set and booleans `True` and `False` with ids
            as given in the models' constants
        """
        # Get the correct constants from the actual models
        from brubeck.models import ValueSet, Value
        BOOLEAN = ValueSet.BOOLEAN
        TRUE = Value.TRUE
        FALSE = Value.FALSE

        # Then replace them with their orm counterparts
        ValueSet, Value = orm['brubeck.ValueSet'], orm['brubeck.Value']

        boolean, _ = ValueSet.objects.get_or_create(id=BOOLEAN, name='boolean')
        Value.objects.get_or_create(id=TRUE, name='True', value_set=boolean)
        Value.objects.get_or_create(id=FALSE, name='False', value_set=boolean)

        # Since we've manually inserted things, the pk sequence is probably off
        try:
            from django.db import connection, transaction
            cursor = connection.cursor()
            cursor.execute("SELECT setval('brubeck_value_id_seq', (SELECT MAX(id) FROM brubeck_value)+1)")
            cursor.execute("SELECT setval('brubeck_valueset_id_seq', (SELECT MAX(id) FROM brubeck_valueset)+1)")
            transaction.commit_unless_managed()
        except Exception as e:
            print 'Unable to update id sequence for Value / ValueSet ' +\
                  'objects. Got error %s' % e


    def backwards(self, orm):
        # Deletes the boolean objects
        from brubeck.models import ValueSet
        BOOLEAN = ValueSet.BOOLEAN

        ValueSet = orm['brubeck.ValueSet']

        ValueSet.objects.get(id=BOOLEAN, name='Boolean').delete()

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'brubeck.document': {
            'Meta': {'object_name': 'Document'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_touched': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'namespace': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'restrictions': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'revision': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['brubeck.Revision']", 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'brubeck.implication': {
            'Meta': {'object_name': 'Implication'},
            'antecedent': ('brubeck.logic.formula.fields.FormulaField', [], {'max_length': '1024'}),
            'consequent': ('brubeck.logic.formula.fields.FormulaField', [], {'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reverses': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'brubeck.profile': {
            'Meta': {'object_name': 'Profile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'brubeck.proof': {
            'Meta': {'object_name': 'Proof', '_ormbases': ['brubeck.Snippet']},
            'proof_agent': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'proof_text': ('django.db.models.fields.TextField', [], {}),
            'snippet_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['brubeck.Snippet']", 'unique': 'True', 'primary_key': 'True'})
        },
        'brubeck.property': {
            'Meta': {'object_name': 'Property'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'values': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': "orm['brubeck.ValueSet']"})
        },
        'brubeck.revision': {
            'Meta': {'object_name': 'Revision'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['brubeck.Document']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['brubeck.Revision']", 'null': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'brubeck.snippet': {
            'Meta': {'object_name': 'Snippet'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['brubeck.Document']", 'unique': 'True', 'primary_key': 'True'}),
            'flags': ('brubeck.fields.SetField', [], {'default': "'||'", 'max_length': '255'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'brubeck.space': {
            'Meta': {'object_name': 'Space'},
            'fully_defined': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'brubeck.trait': {
            'Meta': {'unique_together': "(('space', 'property'),)", 'object_name': 'Trait'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'property': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['brubeck.Property']"}),
            'space': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['brubeck.Space']"}),
            'value': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['brubeck.Value']"})
        },
        'brubeck.value': {
            'Meta': {'unique_together': "(('name', 'value_set'),)", 'object_name': 'Value'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'value_set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'values'", 'to': "orm['brubeck.ValueSet']"})
        },
        'brubeck.valueset': {
            'Meta': {'object_name': 'ValueSet'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['brubeck']
    symmetrical = True
