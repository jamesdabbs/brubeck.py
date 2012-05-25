# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ValueSet'
        db.create_table('brubeck_valueset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('brubeck', ['ValueSet'])

        # Adding model 'Value'
        db.create_table('brubeck_value', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value_set', self.gf('django.db.models.fields.related.ForeignKey')(related_name='values', to=orm['brubeck.ValueSet'])),
        ))
        db.send_create_signal('brubeck', ['Value'])

        # Adding unique constraint on 'Value', fields ['name', 'value_set']
        db.create_unique('brubeck_value', ['name', 'value_set_id'])

        # Adding model 'Space'
        db.create_table('brubeck_space', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('brubeck', ['Space'])

        # Adding model 'Property'
        db.create_table('brubeck_property', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('values', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['brubeck.ValueSet'])),
        ))
        db.send_create_signal('brubeck', ['Property'])

        # Adding model 'Document'
        db.create_table('brubeck_document', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('restrictions', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('last_touched', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('revision', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['brubeck.Revision'], null=True)),
            ('namespace', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('brubeck', ['Document'])

        # Adding model 'Revision'
        db.create_table('brubeck_revision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['brubeck.Document'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('comment', self.gf('django.db.models.fields.TextField')()),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['brubeck.Revision'], null=True)),
        ))
        db.send_create_signal('brubeck', ['Revision'])

        # Adding model 'Snippet'
        db.create_table('brubeck_snippet', (
            ('document_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['brubeck.Document'], unique=True, primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('flags', self.gf('brubeck.fields.SetField')(default='||', max_length=255)),
        ))
        db.send_create_signal('brubeck', ['Snippet'])

        # Adding model 'Proof'
        db.create_table('brubeck_proof', (
            ('snippet_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['brubeck.Snippet'], unique=True, primary_key=True)),
            ('proof_agent', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('brubeck', ['Proof'])

        # Adding model 'Trait'
        db.create_table('brubeck_trait', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('space', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['brubeck.Space'])),
            ('property', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['brubeck.Property'])),
            ('value', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['brubeck.Value'])),
        ))
        db.send_create_signal('brubeck', ['Trait'])

        # Adding model 'Implication'
        db.create_table('brubeck_implication', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('antecedent', self.gf('brubeck.logic.formula.fields.FormulaField')(max_length=1024)),
            ('consequent', self.gf('brubeck.logic.formula.fields.FormulaField')(max_length=1024)),
        ))
        db.send_create_signal('brubeck', ['Implication'])

        # Adding model 'Profile'
        db.create_table('brubeck_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
        ))
        db.send_create_signal('brubeck', ['Profile'])


    def backwards(self, orm):
        # Removing unique constraint on 'Value', fields ['name', 'value_set']
        db.delete_unique('brubeck_value', ['name', 'value_set_id'])

        # Deleting model 'ValueSet'
        db.delete_table('brubeck_valueset')

        # Deleting model 'Value'
        db.delete_table('brubeck_value')

        # Deleting model 'Space'
        db.delete_table('brubeck_space')

        # Deleting model 'Property'
        db.delete_table('brubeck_property')

        # Deleting model 'Document'
        db.delete_table('brubeck_document')

        # Deleting model 'Revision'
        db.delete_table('brubeck_revision')

        # Deleting model 'Snippet'
        db.delete_table('brubeck_snippet')

        # Deleting model 'Proof'
        db.delete_table('brubeck_proof')

        # Deleting model 'Trait'
        db.delete_table('brubeck_trait')

        # Deleting model 'Implication'
        db.delete_table('brubeck_implication')

        # Deleting model 'Profile'
        db.delete_table('brubeck_profile')


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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'brubeck.profile': {
            'Meta': {'object_name': 'Profile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'brubeck.proof': {
            'Meta': {'object_name': 'Proof', '_ormbases': ['brubeck.Snippet']},
            'proof_agent': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'brubeck.trait': {
            'Meta': {'object_name': 'Trait'},
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